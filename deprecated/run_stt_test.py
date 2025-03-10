# Blob audio file > Whisper (STT) > Blob Text > GPT-4o (Refinement) > Blob Text > Bing Search (for RAG) > GPT-4o (Feedback) > Blob Text

import os
import dotenv
from openai import AzureOpenAI
import azure.cognitiveservices.speech as speechsdk
import time
import tiktoken



dotenv.load_dotenv(override = True)
AUDIO_FILE_PATH = os.getenv("AUDIO_FILE_PATH")
AUDIO_FILE_NAME = os.getenv("AUDIO_FILE_NAME")
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
    
    # Configure speech recognizer
    speech_config = speechsdk.SpeechConfig(subscription=AI_SERVICES_SPEECH_KEY, region=AI_SERVICES_SPEECH_REGION)
    speech_config.speech_recognition_language = "ko-KR"
    audio_config = speechsdk.audio.AudioConfig(filename=audio_file_path)

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




def call_gpt_for_refinement(pitch_purpose, stt_chunk):
    max_tokens = 1000

    system_prompt = "STT 퀄리티 개선을 위해 잘못 변환된 단어만을 수정해줘."
    user_base_prompt = f"{pitch_purpose}라는 피치 목적을 고려해, STT 과정에서 잘못 변환된 단어들만 수정해. 예를 들어, '코파이엇'을 '코파일럿'으로 수정. 내용 자체를 바꾸지 마. 수정된 표현을 강조하지 마. 텍스트: "
    user_prompt = user_base_prompt + stt_chunk
    
    encoding = tiktoken.get_encoding("cl100k_base")
    if len(encoding.encode(system_prompt+user_prompt)) <= max_tokens/2:
        refined_text = call_gpt(system_prompt, user_prompt, max_tokens)
        print("Refined: ", refined_text)
        return refined_text
    else:
        # TODO: Implement chunking for large text
        print("Token limit exceeded.")
        return stt_chunk



def refine_stt(pitch_purpose, recognized_chunks):
    refined_text = ""
    refined_chunks = []

    for chunk in recognized_chunks:
        refined_chunk = call_gpt_for_refinement(pitch_purpose, chunk)
        refined_chunks.append(refined_chunk)
        refined_text += refined_chunk + " "
    
    return refined_text, refined_chunks



def run_stt_flow(pitch_purpose):

    # STT
    recognized_text, recognized_chunks = call_stt(AUDIO_FILE_PATH + AUDIO_FILE_NAME)
    print(f"Recognized Text: {recognized_text}")

    # Refine transcription
    refined_text, refined_chunks = refine_stt(pitch_purpose, recognized_chunks)
    print(f"Refined Text: {refined_text}")
    
    # TODO: Use Bing Search for RAG based Feedback
