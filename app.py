import os
import re
from flask import Flask, render_template, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
from google import genai  # NEW SDK IMPORT

app = Flask(__name__)

# Initialize the new Client
# It will automatically find your GEMINI_API_KEY environment variable
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

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
    
    # TRANSCRIPT LOGIC
    try:
        cookie_path = 'youtube_cookies.txt'
        # Use cookies if available to bypass YouTube bot blocking
        if os.path.exists(cookie_path):
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id, cookies=cookie_path)
        else:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        # Priority: Manual English -> Auto English -> Translation
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
        return jsonify({"error": f"YouTube blocked the request. Try uploading fresh youtube_cookies.txt."}), 400
    
    # AI GENERATION (NEW SDK SYNTAX)
    try:
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=f"Write VERY DETAILED textbook-style notes. DO NOT SUMMARIZE. Explain every concept in depth with headings and examples based on this: {transcript_text}"
        )
        return jsonify({"notes": response.text})
    except Exception as e:
        return jsonify({"error": "AI Model Error. Check your API Key."}), 500

if __name__ == '__main__':
    app.run(debug=True)
