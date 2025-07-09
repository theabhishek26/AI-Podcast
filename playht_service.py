import os
import requests
import logging
import time

class PlayHTService:
    def __init__(self):
        self.api_key = os.getenv("PLAYHT_API_KEY", "")
        self.user_id = os.getenv("PLAYHT_USER_ID", "")
        self.base_url = "https://api.play.ht/api"
        
        if not self.api_key or not self.user_id:
            logging.warning("Play HT API credentials not found in environment variables")
    
    def generate_audio(self, text, voice="en-US-JennyNeural", voice2=None, turn_prefix="Alex:", turn_prefix2="Jordan:"):
        """
        Generate audio from text using Play HT API
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
        
        # Use the v1 TTS endpoint as specified in the documentation
        payload = {
            'model': 'PlayDialog',
            'text': text,
            'voice': voice,
            'outputFormat': 'mp3',
            'speed': 1.0
        }
        
        # Add dual-voice support if second voice is provided
        if voice2:
            payload['voice2'] = voice2
            payload['turnPrefix'] = turn_prefix
            payload['turnPrefix2'] = turn_prefix2
        
        try:
            # Use the v1 endpoint as documented
            response = requests.post(
                f"{self.base_url}/v1/tts",
                json=payload,
                headers=headers
            )
            
            if response.status_code == 201:
                job_data = response.json()
                job_id = job_data.get('id')
                
                if job_id:
                    # Poll for completion using the v1 status endpoint
                    return self._poll_job_completion_v1(job_id, headers)
                else:
                    return {
                        'success': False,
                        'error': 'No job ID returned from Play HT API'
                    }
            else:
                return {
                    'success': False,
                    'error': f'API request failed with status {response.status_code}: {response.text}'
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
    
    def get_voices(self):
        """
        Get available voices from Play HT API using v1 endpoint
        """
        if not self.api_key or not self.user_id:
            return []
        
        headers = {
            'X-USER-ID': self.user_id,
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        try:
            # Use v1 endpoint as specified in documentation
            response = requests.get(
                f"{self.base_url}/v1/voices",
                headers=headers
            )
            
            if response.status_code == 200:
                voices_data = response.json()
                # Extract and format voices for the dropdown
                formatted_voices = []
                
                for voice in voices_data:
                    formatted_voices.append({
                        'id': voice.get('id', ''),
                        'name': voice.get('name', 'Unknown Voice'),
                        'language': voice.get('language', 'Unknown'),
                        'gender': voice.get('gender', 'Unknown'),
                        'accent': voice.get('accent', ''),
                        'description': voice.get('description', ''),
                        'sample': voice.get('sample', ''),
                        'tags': voice.get('tags', []),
                        'categories': voice.get('categories', [])
                    })
                
                return formatted_voices
            else:
                logging.error(f"Failed to get voices: {response.status_code} - {response.text}")
                return []
        
        except Exception as e:
            logging.error(f"Error getting voices: {e}")
            return []
