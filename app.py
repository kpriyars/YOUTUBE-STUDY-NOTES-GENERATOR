import os
import requests
from flask import Flask, render_template, request, jsonify
from google import genai

app = Flask(__name__)
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def get_video_id(url):
    import re
    reg = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
    match = re.search(reg, url)
    return match.group(1) if match else None

@app.route('/generate', methods=['POST'])
def handle_generation():
    video_url = request.json.get('url')
    video_id = get_video_id(video_url)
    
    # 1. Ask Scrapingdog for the transcript
    # They handle all the "bot detection" and "sign-in" blocks for you.
    sd_api_key = os.environ.get("SCRAPINGDOG_API_KEY")
    sd_url = "https://api.scrapingdog.com/youtube/transcripts/"
    params = {"api_key": sd_api_key, "v": video_id}
    
    try:
        response = requests.get(sd_url, params=params)
        data = response.json()
        
        # Extract the text from the API response
        transcript_text = " ".join([item['text'] for item in data])
        
        # 2. Give that text to Gemini for the notes
        notes_response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=f"Write long, detailed textbook notes for: {transcript_text}"
        )
        
        return jsonify({"notes": notes_response.text})

    except Exception as e:
        return jsonify({"error": "External API failure. Check credits or key."}), 500
