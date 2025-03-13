import io
import os
import time
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, ContainerClient, BlobBlock, BlobClient, StandardBlobTier
from flask import Flask, request, jsonify

def upload_wav_stream_to_blob(file, filename: str):
    load_dotenv()  # to load variables from .env

    # set variables
    ACCOUNT_URL = os.getenv("BLOB_ACCOUNT_URL")
    CONTAINER_NAME = os.getenv("BLOB_CONTAINER_NAME")

    # connect with blob storage
    credential = DefaultAzureCredential()
    blob_service_client = BlobServiceClient(account_url=ACCOUNT_URL, credential=credential)

    # set file name
    timestamp = int(time.time())
    file_name = filename[0:-4]
    blob_file_name = f'{file_name}_{timestamp}.wav'

    # connect with blob
    blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=blob_file_name)
    
    try: 
        input_stream = io.BytesIO(file.read())
        input_stream.seek(0)
    
        blob_client.upload_blob(input_stream, blob_type="BlockBlob")
    
        # make blob_url
        blob_url = f'{ACCOUNT_URL}/{CONTAINER_NAME}/{blob_file_name}'
        return blob_url
    except Exception as e:
        print(f"uploading error: {e}")
    
    return None
