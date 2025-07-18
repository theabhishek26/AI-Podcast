import os
import requests
import logging
import time

class PlayHTService:
    def __init__(self):
        self.api_key = os.getenv("PLAYHT_API_KEY", "")
        self.user_id = os.getenv("PLAYHT_USER_ID", "")
        self.base_url = "https://api.play.ai/api"
        
        if not self.api_key or not self.user_id:
            logging.warning("Play HT API credentials not found in environment variables")
    
    def generate_audio(self, text, voice1, voice2=None, turn_prefix="Alex:", turn_prefix2="Jordan:"):
        """
        Generate audio from text using Play HT API v1 TTS endpoint
        """
        if not self.api_key or not self.user_id:
            return {
                'success': False,
                'error': 'Play HT API credentials not configured. Please set PLAYHT_API_KEY and PLAYHT_USER_ID environment variables.'
            }
        
        headers = {
            'X-USER-ID': self.user_id,
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        # Build payload based on PlayHT API v1 documentation
        payload = {
            'model': 'PlayDialog',  # Use PlayDialog for multi-turn conversations
            'text': text,
            'voice': voice1,
            'outputFormat': 'mp3',
            'speed': 1.0,
            'language': 'english'  # Default to English, can be parameterized later
        }
        
        # Add dual-voice support if second voice is provided
        if voice2 and voice2 != voice1:
            payload['voice2'] = voice2
            payload['turnPrefix'] = turn_prefix
            payload['turnPrefix2'] = turn_prefix2
            logging.info(f"Generating dual-voice audio with voices: {voice1} and {voice2}")
        else:
            logging.info(f"Generating single-voice audio with voice: {voice1}")
        
        try:
            # Create TTS job using v1 endpoint
            response = requests.post(
                f"{self.base_url}/v1/tts",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 201:
                job_data = response.json()
                job_id = job_data.get('id')
                
                if job_id:
                    logging.info(f"TTS job created with ID: {job_id}")
                    # Poll for completion using the v1 status endpoint
                    return self._poll_job_completion_v1(job_id, headers)
                else:
                    return {
                        'success': False,
                        'error': 'No job ID returned from Play HT API'
                    }
            elif response.status_code == 400:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {'error': response.text}
                return {
                    'success': False,
                    'error': f'Bad request: {error_data.get("error", "Invalid parameters")}'
                }
            elif response.status_code == 401:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                error_message = error_data.get('errorMessage', 'Invalid API credentials')
                
                if 'API access is not available' in error_message:
                    return {
                        'success': False,
                        'error': 'PlayHT API access requires a paid plan. Please upgrade at https://play.ai/pricing to enable podcast generation.'
                    }
                else:
                    return {
                        'success': False,
                        'error': f'Authentication failed: {error_message}'
                    }
            elif response.status_code == 429:
                return {
                    'success': False,
                    'error': 'Rate limit exceeded. Please try again later.'
                }
            else:
                return {
                    'success': False,
                    'error': f'API request failed with status {response.status_code}: {response.text}'
                }
            
        except requests.exceptions.Timeout:
            logging.error("Timeout while creating TTS job")
            return {
                'success': False,
                'error': 'Request timeout. Please try again.'
            }
        except requests.exceptions.RequestException as e:
            logging.error(f"Request error: {e}")
            return {
                'success': False,
                'error': f'Network error: {str(e)}'
            }
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }
    
    def _poll_job_completion(self, job_id, headers):
        """Poll v2 job completion"""
        max_attempts = 60  # 5 minutes max
        attempt = 0
        
        while attempt < max_attempts:
            try:
                status_response = requests.get(
                    f"{self.base_url}/v2/tts/{job_id}",
                    headers=headers
                )
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    job_status = status_data.get('status')
                    
                    if job_status == 'completed':
                        audio_url = status_data.get('output', {}).get('url')
                        if audio_url:
                            return {
                                'success': True,
                                'audio_url': audio_url,
                                'job_id': job_id
                            }
                    elif job_status == 'failed':
                        error_msg = status_data.get('error', 'Unknown error')
                        return {
                            'success': False,
                            'error': f'Job failed: {error_msg}'
                        }
                
                time.sleep(5)
                attempt += 1
                
            except Exception as e:
                logging.error(f"Status check error: {e}")
                time.sleep(5)
                attempt += 1
        
        return {
            'success': False,
            'error': 'Job timed out waiting for completion'
        }
    
    def _poll_job_completion_v1(self, job_id, headers):
        """Poll v1 job completion"""
        max_attempts = 60  # 5 minutes max
        attempt = 0
        
        while attempt < max_attempts:
            try:
                # Use the correct status endpoint for v1 API
                status_response = requests.get(
                    f"{self.base_url}/v1/async/{job_id}",
                    headers=headers
                )
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    
                    # Check if job is completed
                    if status_data.get('completedAt'):
                        output = status_data.get('output', {})
                        audio_url = output.get('url')
                        if audio_url:
                            return {
                                'success': True,
                                'audio_url': audio_url,
                                'job_id': job_id
                            }
                        else:
                            return {
                                'success': False,
                                'error': 'Audio generation completed but no URL provided'
                            }
                    
                    # Check for explicit failure
                    if status_data.get('error'):
                        return {
                            'success': False,
                            'error': f'Job failed: {status_data.get("error")}'
                        }
                    
                    # Job still processing, wait and retry
                    logging.info(f"Job {job_id} still processing, attempt {attempt + 1}")
                    time.sleep(5)
                    attempt += 1
                
                else:
                    logging.error(f"Status check failed: {status_response.status_code} - {status_response.text}")
                    time.sleep(5)
                    attempt += 1
                
            except Exception as e:
                logging.error(f"Status check error: {e}")
                time.sleep(5)
                attempt += 1
        
        return {
            'success': False,
            'error': 'Job timed out waiting for completion'
        }
    
    def get_voices(self, retry_count=3):
        """
        Get available voices from Play HT API using v1 endpoint with retry logic
        """
        if not self.api_key or not self.user_id:
            logging.warning("PlayHT API credentials not available")
            return []
        
        headers = {
            'X-USER-ID': self.user_id,
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        for attempt in range(retry_count):
            try:
                # Use v1 endpoint as specified in documentation
                response = requests.get(
                    f"{self.base_url}/v1/voices",
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    voices_data = response.json()
                    logging.info(f"Successfully fetched {len(voices_data)} voices from PlayHT API")
                    
                    # Extract and format voices for the dropdown
                    formatted_voices = []
                    
                    for voice in voices_data:
                        # Ensure we have the required fields
                        voice_id = voice.get('id', '')
                        voice_name = voice.get('name', 'Unknown Voice')
                        
                        if voice_id and voice_name:
                            formatted_voices.append({
                                'id': voice_id,
                                'name': voice_name,
                                'language': voice.get('language', 'unknown'),
                                'gender': voice.get('gender', 'unknown'),
                                'accent': voice.get('accent', ''),
                                'description': voice.get('description', ''),
                                'sample': voice.get('sample', ''),
                                'tags': voice.get('tags', []),
                                'categories': voice.get('categories', []),
                                'updatedDate': voice.get('updatedDate', 0),
                                'createdDate': voice.get('createdDate', 0)
                            })
                    
                    # Sort voices by language, then by name
                    formatted_voices.sort(key=lambda x: (x['language'], x['name']))
                    logging.info(f"Formatted {len(formatted_voices)} voices for use")
                    return formatted_voices
                
                elif response.status_code == 401:
                    logging.error("Invalid API credentials for PlayHT")
                    return []
                
                elif response.status_code == 503:
                    logging.warning(f"PlayHT API temporarily unavailable (503) - attempt {attempt + 1}/{retry_count}")
                    if attempt < retry_count - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    else:
                        logging.error("PlayHT API unavailable after all retry attempts")
                        return []
                
                else:
                    logging.error(f"Failed to get voices: {response.status_code} - {response.text}")
                    return []
            
            except requests.exceptions.Timeout:
                logging.error(f"Timeout while fetching voices from PlayHT API - attempt {attempt + 1}/{retry_count}")
                if attempt < retry_count - 1:
                    time.sleep(2)
                    continue
                else:
                    return []
            
            except requests.exceptions.RequestException as e:
                logging.error(f"Request error while fetching voices: {e}")
                if attempt < retry_count - 1:
                    time.sleep(2)
                    continue
                else:
                    return []
            
            except Exception as e:
                logging.error(f"Unexpected error getting voices: {e}")
                return []
        
        return []
