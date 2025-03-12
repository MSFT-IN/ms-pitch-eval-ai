import os
from dotenv import load_dotenv
from continuous_recognition import extract_data
from blob_uploader import upload_wav_to_blob

load_dotenv()  # to load variables from .env

# recognition test
scores = extract_data()
print('scores: ', scores)

# upload test
url = upload_wav_to_blob(os.getenv("AUDIO_FILE"))
print('url: ', url)