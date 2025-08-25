"""
Flask TTS Application with Male and Female Voice Options
Combines multiple TTS services to provide gender-specific voices
"""

from flask import Flask, render_template, request, jsonify, send_file
import os
import uuid
import tempfile
import requests
from gtts import gTTS
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except:
    PYTTSX3_AVAILABLE = False

app = Flask(__name__)

# Use system temp directory
TEMP_DIR = tempfile.gettempdir()

# StreamElements voices (free, no API key required)
STREAMELEMENTS_VOICES = {
    # Male voices
    "Brian": {"gender": "Male", "accent": "British", "provider": "se"},
    "Daniel": {"gender": "Male", "accent": "British", "provider": "se"},
    "George": {"gender": "Male", "accent": "British", "provider": "se"},
    "Matthew": {"gender": "Male", "accent": "American", "provider": "se"},
    "Russell": {"gender": "Male", "accent": "Australian", "provider": "se"},
    "Justin": {"gender": "Male", "accent": "American Teen", "provider": "se"},
    "Joey": {"gender": "Male", "accent": "American", "provider": "se"},
    # Female voices
    "Emma": {"gender": "Female", "accent": "British", "provider": "se"},
    "Amy": {"gender": "Female", "accent": "British", "provider": "se"},
    "Salli": {"gender": "Female", "accent": "American", "provider": "se"},
    "Joanna": {"gender": "Female", "accent": "American", "provider": "se"},
    "Kendra": {"gender": "Female", "accent": "American", "provider": "se"},
    "Kimberly": {"gender": "Female", "accent": "American", "provider": "se"},
    "Ivy": {"gender": "Female", "accent": "American Child", "provider": "se"},
    "Nicole": {"gender": "Female", "accent": "Australian", "provider": "se"},
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_voices', methods=['GET'])
def get_voices():
    """Return available voices from multiple sources"""
    voice_dict = {
        "Male Voices - British": [
            {'name': 'Brian', 'display': 'Brian - British Male (Clear)', 'gender': 'Male'},
            {'name': 'Daniel', 'display': 'Daniel - British Male (Deep)', 'gender': 'Male'},
            {'name': 'George', 'display': 'George - British Male (Mature)', 'gender': 'Male'},
        ],
        "Male Voices - American": [
            {'name': 'Matthew', 'display': 'Matthew - American Male (Neutral)', 'gender': 'Male'},
            {'name': 'Joey', 'display': 'Joey - American Male (Casual)', 'gender': 'Male'},
            {'name': 'Justin', 'display': 'Justin - American Male (Young)', 'gender': 'Male'},
        ],
        "Male Voices - Other": [
            {'name': 'Russell', 'display': 'Russell - Australian Male', 'gender': 'Male'},
        ],
        "Female Voices - British": [
            {'name': 'Emma', 'display': 'Emma - British Female (Clear)', 'gender': 'Female'},
            {'name': 'Amy', 'display': 'Amy - British Female (Warm)', 'gender': 'Female'},
        ],
        "Female Voices - American": [
            {'name': 'Salli', 'display': 'Salli - American Female (Clear)', 'gender': 'Female'},
            {'name': 'Joanna', 'display': 'Joanna - American Female (Neutral)', 'gender': 'Female'},
            {'name': 'Kendra', 'display': 'Kendra - American Female (Professional)', 'gender': 'Female'},
            {'name': 'Kimberly', 'display': 'Kimberly - American Female (Warm)', 'gender': 'Female'},
            {'name': 'Ivy', 'display': 'Ivy - American Female (Young)', 'gender': 'Female'},
        ],
        "Female Voices - Other": [
            {'name': 'Nicole', 'display': 'Nicole - Australian Female', 'gender': 'Female'},
        ],
        "Google TTS - Accents (Neutral)": [
            {'name': 'gtts-us', 'display': 'Google US English', 'gender': 'Neutral'},
            {'name': 'gtts-uk', 'display': 'Google UK English', 'gender': 'Neutral'},
            {'name': 'gtts-au', 'display': 'Google Australian', 'gender': 'Neutral'},
            {'name': 'gtts-in', 'display': 'Google Indian English', 'gender': 'Neutral'},
            {'name': 'gtts-ca', 'display': 'Google Canadian', 'gender': 'Neutral'},
            {'name': 'gtts-ie', 'display': 'Google Irish', 'gender': 'Neutral'},
            {'name': 'gtts-za', 'display': 'Google South African', 'gender': 'Neutral'},
        ]
    }
    
    # Add system voices if pyttsx3 is available
    if PYTTSX3_AVAILABLE:
        try:
            engine = pyttsx3.init()
            system_voices = engine.getProperty('voices')
            if system_voices:
                voice_dict["System Voices"] = []
                for voice in system_voices[:10]:  # Limit to first 10
                    name = voice.name.split('.')[-1] if '.' in voice.name else voice.name
                    voice_dict["System Voices"].append({
                        'name': f'system-{voice.id}',
                        'display': f'{name} (System)',
                        'gender': 'Male' if 'male' in voice.name.lower() else 'Female'
                    })
        except:
            pass
    
    return jsonify(voice_dict)

@app.route('/synthesize', methods=['POST'])
def synthesize():
    """Convert text to speech using appropriate service"""
    try:
        data = request.json
        text = data.get('text', '').strip()
        voice = data.get('voice', 'gtts-us')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        # Generate unique filename
        filename = f"tts_{uuid.uuid4().hex[:8]}.mp3"
        filepath = os.path.join(TEMP_DIR, filename)
        
        print(f"Generating TTS with voice: {voice}")
        
        # StreamElements voices
        if voice in STREAMELEMENTS_VOICES:
            print(f"Using StreamElements voice: {voice}")
            
            url = "https://api.streamelements.com/kappa/v2/speech"
            params = {
                "voice": voice,
                "text": text
            }
            
            response = requests.get(url, params=params, stream=True)
            
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
                print(f"StreamElements audio saved to: {filepath}")
            else:
                raise Exception(f"StreamElements API failed: {response.status_code}")
                
        # System voices (pyttsx3)
        elif voice.startswith('system-') and PYTTSX3_AVAILABLE:
            voice_id = voice.replace('system-', '')
            print(f"Using system voice: {voice_id}")
            
            engine = pyttsx3.init()
            engine.setProperty('voice', voice_id)
            engine.setProperty('rate', 150)
            
            # Save as WAV first
            wav_filepath = filepath.replace('.mp3', '.wav')
            engine.save_to_file(text, wav_filepath)
            engine.runAndWait()
            
            # Try to convert to MP3
            try:
                from pydub import AudioSegment
                audio = AudioSegment.from_wav(wav_filepath)
                audio.export(filepath, format="mp3", bitrate="128k")
                os.remove(wav_filepath)
            except:
                # If conversion fails, just rename
                os.rename(wav_filepath, filepath)
                
        # Google TTS voices
        else:
            # Map voice codes to TLDs for different accents
            tld_map = {
                'gtts-us': 'com',
                'gtts-uk': 'co.uk',
                'gtts-au': 'com.au',
                'gtts-in': 'co.in',
                'gtts-ca': 'ca',
                'gtts-ie': 'ie',
                'gtts-za': 'co.za'
            }
            
            tld = tld_map.get(voice, 'com')
            print(f"Using gTTS with TLD: {tld}")
            
            tts = gTTS(text=text, lang='en', tld=tld, slow=False)
            tts.save(filepath)
            print(f"gTTS audio saved to: {filepath}")
        
        return jsonify({
            'success': True,
            'filename': filename
        })
        
    except Exception as e:
        print(f"Error in synthesis: {str(e)}")
        
        # Fallback to basic gTTS
        try:
            print("Falling back to basic gTTS...")
            filename = f"tts_{uuid.uuid4().hex[:8]}.mp3"
            filepath = os.path.join(TEMP_DIR, filename)
            tts = gTTS(text=text, lang='en')
            tts.save(filepath)
            return jsonify({
                'success': True,
                'filename': filename,
                'note': 'Used fallback voice'
            })
        except Exception as fallback_error:
            return jsonify({'error': f'All synthesis methods failed: {str(e)}'}), 500

@app.route('/download/<filename>')
def download(filename):
    """Download the generated audio file"""
    try:
        if not all(c.isalnum() or c in '._-' for c in filename):
            return jsonify({'error': 'Invalid filename'}), 400
            
        filepath = os.path.join(TEMP_DIR, filename)
        if os.path.exists(filepath) and filename.endswith('.mp3'):
            return send_file(
                filepath,
                mimetype='audio/mpeg',
                as_attachment=True,
                download_name=f"tts_output_{uuid.uuid4().hex[:8]}.mp3"
            )
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/audio/<filename>')
def serve_audio(filename):
    """Serve audio file for preview"""
    try:
        if not all(c.isalnum() or c in '._-' for c in filename):
            return jsonify({'error': 'Invalid filename'}), 400
            
        filepath = os.path.join(TEMP_DIR, filename)
        if os.path.exists(filepath) and filename.endswith('.mp3'):
            return send_file(filepath, mimetype='audio/mpeg')
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print(f"Starting Multi-Service TTS server...")
    print(f"Temp directory: {TEMP_DIR}")
    print(f"Services available:")
    print("  - StreamElements: Male and Female voices")
    print("  - Google TTS: Multiple accents")
    if PYTTSX3_AVAILABLE:
        print("  - System TTS: Local voices")
    app.run(debug=True, host='0.0.0.0', port=5050)