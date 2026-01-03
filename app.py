import os
import re
from flask import Flask, render_template, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

def extract_video_id(url):
    pattern = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
    match = re.search(pattern, url)
    return match.group(1) if match else None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def handle_generation():
    data = request.json
    video_url = data.get('url')
    video_id = extract_video_id(video_url)
    
    if not video_id:
        return jsonify({"error": "Invalid YouTube URL"}), 400
    
    # ULTIMATE TRANSCRIPT FETCHING LOGIC
    try:
        # Check if cookie file exists
        cookie_path = 'youtube_cookies.txt'
        
        # If the file is on GitHub/Render, use it to bypass blocks
        if os.path.exists(cookie_path):
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id, cookies=cookie_path)
        else:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        # Try English Manual, then English Auto, then Translate any other to English
        try:
            transcript = transcript_list.find_manually_created_transcript(['en'])
        except:
            try:
                transcript = transcript_list.find_generated_transcript(['en'])
            except:
                transcript = transcript_list.find_transcript(['en']).translate('en')

        transcript_data = transcript.fetch()
        transcript_text = " ".join([t['text'] for t in transcript_data])
        
    except Exception as e:
        return jsonify({"error": f"YouTube is still blocking this. Error details: {str(e)}"}), 400
    
    # AI Generation
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        Write VERY DETAILED textbook-style notes. 
        - DO NOT SUMMARIZE. 
        - Explain every single concept in the transcript.
        - Use H1, H2, H3, and long paragraphs.
        - Provide definitions and examples.
        Transcript: {transcript_text}
        """
        response = model.generate_content(prompt)
        return jsonify({"notes": response.text})
    except Exception as e:
        return jsonify({"error": "AI Error"}), 500

if __name__ == '__main__':
    app.run(debug=True)
