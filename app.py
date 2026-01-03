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
    
    # NEW SMARTER TRANSCRIPT LOGIC
    try:
        # Get all available transcripts
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        try:
            # 1. Try to find manually created English transcript
            transcript = transcript_list.find_manually_created_transcript(['en'])
        except:
            try:
                # 2. If no manual, try auto-generated English
                transcript = transcript_list.find_generated_transcript(['en'])
            except:
                # 3. If no English at all, find ANY transcript and translate it to English
                # This makes foreign language videos work too!
                transcript = transcript_list.find_transcript(['en']).translate('en')

        transcript_data = transcript.fetch()
        transcript_text = " ".join([t['text'] for t in transcript_data])
        
    except Exception as e:
        # If it still fails, the video truly has zero captions (rare)
        return jsonify({"error": "This video has no captions enabled. Try a video with the 'CC' icon."}), 400
    
    # 2. Generate Detailed Notes via Gemini (Existing Logic)
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"Act as a Senior University Professor. Convert the following transcript into a VERY DETAILED, long-form textbook chapter. DO NOT SUMMARIZE. Explain every point in depth with headings, examples, and key terms: {transcript_text}"
        response = model.generate_content(prompt)
        return jsonify({"notes": response.text})
    except Exception as e:
        return jsonify({"error": "AI Error: " + str(e)}), 500
  
if __name__ == '__main__':
    app.run(debug=True)
