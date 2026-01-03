import os
import re
import yt_dlp
import assemblyai as aai
from flask import Flask, render_template, request, jsonify
from google import genai  # Correct 2026 SDK

app = Flask(__name__)

# 1. SETUP CLIENTS
aai.settings.api_key = os.environ.get("ASSEMBLYAI_API_KEY")

# Fix for the ValueError: explicitly pass the key to the Client
gemini_api_key = os.environ.get("GEMINI_API_KEY")
if not gemini_api_key:
    # This helps you debug in the Render logs
    print("CRITICAL ERROR: GEMINI_API_KEY is missing from environment variables!")
    
client = genai.Client(api_key=gemini_api_key)

def get_audio_url(youtube_url):
    """Bypasses YouTube blocks by using embedded player clients"""
    ydl_opts = {
        'format': 'm4a/bestaudio/best',
        'quiet': True,
        'extractor_args': {'youtube': {'player_client': ['web_embedded', 'web', 'tv']}}
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=False)
        return info['url']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def handle_generation():
    video_url = request.json.get('url')
    
    try:
        # Step 1: Extract Audio URL
        audio_url = get_audio_url(video_url)

        # Step 2: Transcribe (AI hears the video)
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(audio_url)
        
        if transcript.status == aai.TranscriptStatus.error:
            return jsonify({"error": "Transcription failed. Try a shorter video."}), 500
        
        # Step 3: Generate Textbook Notes
        # We use Gemini 1.5 Flash for high detail and speed
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=f"Act as a Professor. Write an extremely long, detailed textbook chapter based on this video text. Do not summarize. Use headings, examples, and deep definitions: {transcript.text}"
        )
        
        return jsonify({"notes": response.text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
