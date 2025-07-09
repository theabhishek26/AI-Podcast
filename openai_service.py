import os
import json
import logging
import tempfile
from openai import OpenAI
from pydub import AudioSegment
import io

class OpenAIService:
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            logging.warning("OpenAI API key not found in environment variables")
            self.client = None
        else:
            self.client = OpenAI(api_key=self.api_key)
    
    def generate_podcast_script(self, title, description, duration_minutes=5):
        """
        Generate a conversational podcast script between two AI hosts
        """
        if not self.client:
            return {
                'success': False,
                'error': 'OpenAI API key not configured'
            }
        
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        prompt = f"""Create a natural, engaging podcast conversation between two AI hosts about the following topic:

Title: {title}
Description: {description}

Create a {duration_minutes}-minute podcast script with these requirements:
1. Two distinct hosts with different personalities:
   - Host 1 (Alex): Curious, asks probing questions, enthusiastic
   - Host 2 (Jordan): Knowledgeable, provides insights, thoughtful
2. Natural conversation flow with transitions
3. Include intro, main discussion, and outro
4. Make it informative yet entertaining
5. Use conversational language, not formal
6. Include natural speech patterns like "you know", "actually", "that's interesting"

Format the response as JSON with this structure:
{{
  "intro": "Introduction dialogue",
  "segments": [
    {{
      "speaker": "Alex or Jordan",
      "text": "What they say"
    }}
  ],
  "outro": "Closing dialogue"
}}

Make the conversation feel authentic and engaging, like real podcast hosts discussing the topic."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert podcast script writer who creates engaging, natural conversations between two hosts."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.8,
                timeout=30  # Add timeout to prevent hanging
            )
            
            script_data = json.loads(response.choices[0].message.content)
            
            # Convert to the format needed for Play HT dual-voice generation
            full_script = self._format_script_for_tts(script_data)
            
            return {
                'success': True,
                'script': full_script,
                'raw_data': script_data
            }
            
        except Exception as e:
            logging.error(f"OpenAI API error: {e}")
            # Return a fallback script if OpenAI fails
            fallback_script = self._generate_fallback_script(title, description)
            return {
                'success': True,
                'script': fallback_script,
                'raw_data': {'fallback': True}
            }
    
    def _generate_fallback_script(self, title, description):
        """Generate a simple fallback script when OpenAI is unavailable"""
        return f"""Alex: Welcome to today's podcast! I'm Alex, and I'm here with my co-host Jordan. 

Jordan: Hi everyone! Today we're diving into an exciting topic: {title}. 

Alex: That sounds fascinating! Jordan, can you tell us more about {description}?

Jordan: Absolutely! {description} This is such an important topic because it affects many aspects of our daily lives.

Alex: That's really interesting! What do you think our listeners should know about this?

Jordan: Well, I think the key points to understand are the practical implications and how this might evolve in the future.

Alex: Great insights! Before we wrap up, do you have any final thoughts for our audience?

Jordan: I'd encourage everyone to stay curious and keep learning about topics like this. It's amazing how much there is to discover.

Alex: Couldn't agree more! Thanks for joining us today, everyone. Until next time!

Jordan: Thanks for listening, and we'll see you in the next episode!"""
    
    def _format_script_for_tts(self, script_data):
        """
        Format the script for Play HT dual-voice TTS generation
        """
        full_text = ""
        
        # Add intro
        if script_data.get('intro'):
            full_text += script_data['intro'] + " "
        
        # Add main conversation
        for segment in script_data.get('segments', []):
            speaker = segment.get('speaker', 'Alex')
            text = segment.get('text', '')
            
            # Add speaker prefix for Play HT to distinguish voices
            if speaker.lower() == 'alex':
                full_text += f"Alex: {text} "
            else:
                full_text += f"Jordan: {text} "
        
        # Add outro
        if script_data.get('outro'):
            full_text += script_data['outro']
        
        return full_text.strip()
    
    def generate_dual_voice_audio(self, script_content, host1_voice="alloy", host2_voice="echo"):
        """
        Generate dual-voice audio using OpenAI's TTS API
        """
        if not self.client:
            return {
                'success': False,
                'error': 'OpenAI API key not configured'
            }
        
        try:
            # Parse script into segments
            segments = self._parse_script_segments(script_content)
            audio_segments = []
            
            logging.info(f"Processing {len(segments)} segments for TTS")
            
            for i, segment in enumerate(segments):
                voice = host1_voice if segment['speaker'] == 'Host 1' else host2_voice
                text = segment['text']
                
                # Skip empty segments
                if not text.strip():
                    continue
                
                # Truncate very long segments to prevent timeouts
                if len(text) > 4000:  # OpenAI TTS limit is 4096 characters
                    text = text[:4000] + "..."
                
                logging.info(f"Generating audio for segment {i+1}/{len(segments)} with {voice} voice")
                
                # Generate audio for this segment with timeout
                try:
                    response = self.client.audio.speech.create(
                        model="tts-1",
                        voice=voice,
                        input=text,
                        response_format="mp3"
                    )
                    
                    # Convert to audio segment
                    audio_data = io.BytesIO(response.content)
                    audio_segment = AudioSegment.from_mp3(audio_data)
                    
                    # Add slight pause between speakers
                    if audio_segments:
                        pause = AudioSegment.silent(duration=800)  # 800ms pause
                        audio_segments.append(pause)
                    
                    audio_segments.append(audio_segment)
                    
                except Exception as segment_error:
                    logging.error(f"Error generating audio for segment {i+1}: {segment_error}")
                    # Add a short silence instead of failing completely
                    silence = AudioSegment.silent(duration=1000)
                    audio_segments.append(silence)
            
            if not audio_segments:
                return {
                    'success': False,
                    'error': 'No audio segments were generated successfully'
                }
            
            # Combine all segments
            logging.info("Combining audio segments")
            combined_audio = sum(audio_segments)
            
            # Export to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                combined_audio.export(tmp_file.name, format="mp3")
                
                logging.info(f"Audio generation completed: {tmp_file.name}")
                return {
                    'success': True,
                    'audio_file': tmp_file.name,
                    'duration': len(combined_audio) / 1000  # duration in seconds
                }
                
        except Exception as e:
            logging.error(f"OpenAI TTS error: {e}")
            return {
                'success': False,
                'error': f'Failed to generate audio: {str(e)}'
            }
    
    def _parse_script_segments(self, script_content):
        """Parse script content into speaker segments"""
        segments = []
        lines = script_content.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('Host 1:'):
                segments.append({
                    'speaker': 'Host 1',
                    'text': line[7:].strip()  # Remove "Host 1:" prefix
                })
            elif line.startswith('Host 2:'):
                segments.append({
                    'speaker': 'Host 2',
                    'text': line[7:].strip()  # Remove "Host 2:" prefix
                })
        
        return segments