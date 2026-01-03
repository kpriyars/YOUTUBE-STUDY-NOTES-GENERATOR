import os
import re
from flask import Flask, render_template, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai

app = Flask(__name__)

# Security: It pulls the key from Render's Environment Variables
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

def extract_video_id(url):
    # Regex to find the 11-character YouTube ID
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
    
    # 1. Fetch Transcript
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        transcript_text = " ".join([t['text'] for t in transcript_list])
    except Exception:
        return jsonify({"error": "Transcript not available for this video."}), 400
    
    # 2. Generate Detailed Notes via Gemini
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        Act as a Senior University Professor. Convert the following transcript into a 
        VERY DETAILED, long-form textbook chapter. 
        
        RULES:
        - DO NOT SUMMARIZE. Explain every point in depth.
        - Use H1 for titles, H2 and H3 for sub-sections.
        - Use bullet points for lists but keep the main explanations in long paragraphs.
        - Add a 'Key Terms' section with definitions.
        - Add an 'Examples' section for complex logic.
        
        TRANSCRIPT:
        {transcript_text}
        """
        response = model.generate_content(prompt)
        return jsonify({"notes": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
