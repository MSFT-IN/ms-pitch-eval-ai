import io
import os
import time
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, ContainerClient, BlobBlock, BlobClient, StandardBlobTier

def upload_wav_to_blob(file_path: str):
    load_dotenv()  # to load variables from .env

    # set variables
    ACCOUNT_URL = os.getenv("BLOB_ACCOUNT_URL")
    CONTAINER_NAME = os.getenv("BLOB_CONTAINER_NAME")

    # check file type
    if not file_path.lower().endswith(".wav"):
        raise ValueError("Only .wav files are allowed.")

    # connect with blob storage
    credential = DefaultAzureCredential()
    blob_service_client = BlobServiceClient(account_url=ACCOUNT_URL, credential=credential)

    # set file name
    timestamp = int(time.time())
    file_name = os.path.basename(file_path)[0:-4]
    blob_file_name = f'{file_name}_{timestamp}.wav'

    # connect with container
    container_client = blob_service_client.get_container_client(container=CONTAINER_NAME)
    with open(file_path, mode="rb") as data:
        blob_client = container_client.upload_blob(name=blob_file_name, data=data, overwrite=True)

    # make blob_url
    blob_url = f'{ACCOUNT_URL}/{CONTAINER_NAME}/{blob_file_name}'
    return blob_url

