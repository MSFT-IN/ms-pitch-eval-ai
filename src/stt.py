# Blob audio file > Whisper (STT) > Blob Text > GPT-4o (Refinement) > Blob Text > Bing Search (for RAG) > GPT-4o (Feedback) > Blob Text

import os
import dotenv
from openai import AzureOpenAI
import requests
import urllib.request
import json
import ssl

# Load environment variables
dotenv.load_dotenv()
AUDIO_FILE_PATH = os.getenv("AUDIO_FILE_PATH")
AUDIO_FILE_NAME = os.getenv("AUDIO_FILE_NAME")
AOAI_ENDPOINT_GPT = os.getenv("AOAI_ENDPOINT_GPT")
AOAI_ENDPOINT_GPT_0513 = os.getenv("AOAI_ENDPOINT_GPT_0513")
AOAI_ENDPOINT_WHISPER = os.getenv("AOAI_ENDPOINT_WHISPER")
AOAI_API_KEY = os.getenv("AOAI_API_KEY")




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
        model = "whisper"
    )

    result = response.text
    return result




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
