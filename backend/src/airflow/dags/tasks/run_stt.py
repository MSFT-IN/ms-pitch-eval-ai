import os
import dotenv
import tiktoken
import sys
sys.path.append(os.path.dirname(__file__))
from base_call import call_gpt, call_stt

dotenv.load_dotenv(override = True)

AUDIO_FILE_PATH = os.getenv("AUDIO_FILE_PATH")
AUDIO_FILE_NAME = os.getenv("AUDIO_FILE_NAME")


def run_basic_stt():
    """
    Function to run STT.
    Args:
        pitch_purpose (str): Purpose of the pitch.
    Returns:
        refined_text (str): Refined STT transcription.
        refined_chunks (list): List of refined text chunks.
    """

    # STT
    recognized_text, recognized_chunks = call_stt(AUDIO_FILE_PATH + AUDIO_FILE_NAME)
    print(f"Recognized Text: {recognized_text}")
    
    return recognized_text, recognized_chunks



def call_gpt_for_refinement(pitch_purpose, stt_chunk):
    """
    Function to call GPT for refining the STT transcription.

    Args:
        pitch_purpose (str): Purpose of the pitch.
        stt_chunk (str): STT chunk to refine.
    Returns:
        refined_text (str): Refined STT chunk.
    """
    
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
    """
    Function to refine the STT transcription.
    Args:
        pitch_purpose (str): Purpose of the pitch.
        recognized_chunks (list): List of recognized text chunks.
    Returns:
        refined_text (str): Refined STT transcription.
        refined_chunks (list): List of refined text chunks.
    """
    refined_text = ""
    refined_chunks = []

    for chunk in recognized_chunks:
        refined_chunk = call_gpt_for_refinement(pitch_purpose, chunk)
        refined_chunks.append(refined_chunk)
        refined_text += refined_chunk + " "
    
    return refined_text, refined_chunks



