import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from continuous_recognition import extract_data
from blob_uploader import upload_wav_stream_to_blob

load_dotenv()  # to load variables from .env

# flask app config
app = Flask(__name__)
CORS(app)

@app.route('/upload', methods=['POST'])
def upload_wav():
    file = request.files.get('file')
    if file:
        upload_url = upload_wav_stream_to_blob(file, file.filename)
        return jsonify({"success": True, "url": upload_url})
    else:
        return jsonify({"error": 400})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

"""
# recognition test
scores = extract_data()
print('scores: ', scores)

# upload test
url = upload_wav_to_blob(os.getenv("AUDIO_FILE"))
print('url: ', url)

## suzy 
from run_stt import run_stt_flow
from content_feedback import run_feedback_flow

if __name__ == "__main__":
    pitch_purpose = "보안을 위한 코파일럿 사용"
    refined_text, refined_chunks = run_stt_flow(pitch_purpose)
    feedback = run_feedback_flow(refined_chunks)
    print("\n\n\nContent Feedback Based on MSLearn:", feedback)

"""