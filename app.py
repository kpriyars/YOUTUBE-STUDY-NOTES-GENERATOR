import os
import re
import yt_dlp
import assemblyai as aai
from flask import Flask, render_template, request, jsonify
from google import genai

app = Flask(__name__)

# Initialize Clients
aai.settings.api_key = os.environ.get("ASSEMBLYAI_API_KEY")
gemini_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def get_audio_url(youtube_url):
    """Gets the raw audio link so the AI can 'listen' to the video"""
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=False)
        return info['url']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def handle_generation():
    data = request.json
    video_url = data.get('url')
    
    try:
        # 1. Get the audio stream
        audio_url = get_audio_url(video_url)

        # 2. Convert Audio to Text (Transcription)
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(audio_url)
        
        if transcript.status == aai.TranscriptStatus.error:
            return jsonify({"error": "AI could not hear the audio clearly."}), 500
        
        # 3. Use the text to create Textbook-Style Notes
        # This prompt is the most important part for quality!
        prompt = f"""
        Act as a Senior University Professor. Use the following text to write 
        VERY DETAILED, long-form textbook-style study notes. 
        
        CRITICAL RULES:
        - DO NOT SUMMARIZE. Explain every point mentioned in depth.
        - Structure with H1 for the Title and H2/H3 for sub-sections.
        - Use long, academic paragraphs.
        - Include a 'Definitions' section for technical terms.
        - Write at least 1000 words if the content allows.
        
        TEXT TO PROCESS:
        {transcript.text}
        """
        
        response = gemini_client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt
        )
        
        return jsonify({"notes": response.text})

    except Exception as e:
        return jsonify({"error": f"Something went wrong: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
