import os
import dotenv
from openai import AzureOpenAI
import azure.cognitiveservices.speech as speechsdk
import time



dotenv.load_dotenv(os.path.join(os.path.dirname(__file__), '../../../.env'))
AOAI_ENDPOINT_GPT = os.getenv("AOAI_ENDPOINT_GPT")
AOAI_ENDPOINT_GPT_0513 = os.getenv("AOAI_ENDPOINT_GPT_0513")
AOAI_ENDPOINT_WHISPER = os.getenv("AOAI_ENDPOINT_WHISPER")
AOAI_API_KEY = os.getenv("AOAI_API_KEY")
AI_SERVICES_SPEECH_KEY = os.getenv("AI_SERVICES_SPEECH_KEY")
AI_SERVICES_SPEECH_REGION = os.getenv("AI_SERVICES_SPEECH_REGION")
AI_SERVICES_SPEECH_ENDPOINT = os.getenv("AI_SERVICES_SPEECH_ENDPOINT")



def call_whisper(audio_file_path):
    """
    Function to convert audio to text using Whisper audio transcription.
    
    Args:
        audio_file_path (str): Path to the audio file, including the file name and extension. e.g., "testfiles/testaudio.mp3"
    Returns:
        result (str): STT result text.
    
    * Uses Azure AI Services OpenAI
    * Reference https://learn.microsoft.com/en-us/azure/ai-services/openai/whisper-quickstart?tabs=command-line%2Cpython-new%2Ckeyless%2Ctypescript-keyless&pivots=programming-language-python
    """
     
    aoai_client_whisper = AzureOpenAI(
        api_key = os.getenv("AOAI_API_KEY"),  
        api_version = "2024-02-01",
        azure_endpoint = os.getenv("AOAI_ENDPOINT_WHISPER")
    )

    response = aoai_client_whisper.audio.transcriptions.create(
        file = open(audio_file_path, "rb"),            
        model = "whisper",
        response_format = "verbose_json"
    )

    result = response.text

    # return result
    return response



def call_stt(audio_file_path):
    """
    Function to convert audio to text using Azure Speech SDK.
    
    Args:
        audio_file_path (str): Path to the audio file, including the file name and extension. e.g., "testfiles/testaudio.mp3"
    Returns:
        recognized_text (str): STT result text.
        recognized_chunks (list): List of recognized text chunks.

    * Uses Azure AI Services Speech SDK
    """
    SPEECH_KEY = os.getenv("AI_SERVICES_SPEECH_KEY")
    SERVICES_REGION = os.getenv("AI_SERVICES_SPEECH_REGION")
    AUDIO_FILE = audio_file_path
    
    if not AUDIO_FILE.lower().endswith(".wav"):
        raise ValueError("Only .wav files are allowed.")
    # set speech config
    speech_config = speechsdk.SpeechConfig(
        subscription=SPEECH_KEY, 
        region=SERVICES_REGION
    )
    
    speech_config.speech_recognition_language = "ko-KR"
 
    # set audio config
    audio_config = speechsdk.audio.AudioConfig(filename=AUDIO_FILE)

    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    # For saving the recognized text
    done = False
    recognized_text = ""
    recognized_chunks = []

    def stop_cb(evt: speechsdk.SessionEventArgs):
        """Callback function called upon session exit"""
        nonlocal done
        print("Session stopped. Checking if end of audio...")

        # End STT if end of audio
        if evt.reason == speechsdk.ResultReason.NoMatch:
            print("End of audio detected. Stopping STT.")
            done = True
        else:
            print("Restarting STT...")
            speech_recognizer.start_continuous_recognition()

    def recognized(evt: speechsdk.SpeechRecognitionEventArgs):
        """Callback function called upon speech recognition"""
        nonlocal recognized_text, recognized_chunks

        # Prevent redundant calls
        if evt.result.text and (not recognized_chunks or evt.result.text != recognized_chunks[-1]):
            recognized_chunks.append(evt.result.text)
            recognized_text += evt.result.text + " "
            print(f"Recognized: {evt.result.text}")

    # Disconnect before reconnecting event (Prevent redundant calls)
    speech_recognizer.recognized.disconnect_all()
    speech_recognizer.session_stopped.disconnect_all()
    speech_recognizer.canceled.disconnect_all()

    speech_recognizer.recognized.connect(recognized)
    speech_recognizer.session_stopped.connect(stop_cb)
    speech_recognizer.canceled.connect(stop_cb)

    # Speech recognized, start transcription
    speech_recognizer.start_continuous_recognition()

    # Delay before stopping session
    timeout = time.time() + 300  # 300seconds limit
    while not done and time.time() < timeout:
        time.sleep(0.5)

    # Force stop
    speech_recognizer.stop_continuous_recognition()

    print(f"Final Recognized Text: {recognized_text}")

    return recognized_text, recognized_chunks



def call_gpt(system_prompt, user_prompt, max_tokens = 500):
    """
    Function to generate text using GPT-4o chat completion.
    
    Args:
        system_prompt (str): System prompt.
        user_prompt (str): User prompt.
        max_tokens (int): Maximum number of tokens to generate, default is 500.
    Returns:
        result (str): Generated text.
    
    * Uses Azure AI Services OpenAI
    """
        
    aoai_client_gpt = AzureOpenAI(
        api_key = os.getenv("AOAI_API_KEY"),  
        api_version = "2024-02-01",
        azure_endpoint = os.getenv("AOAI_ENDPOINT_GPT")
    )

    gpt_input = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    response = aoai_client_gpt.chat.completions.create(
        messages = gpt_input,            
        model = "gpt-4o",
        max_tokens = max_tokens
    )

    result = response.choices[0].message.content
    return result