import os
import matplotlib.pyplot as plt
import numpy as np
import librosa
import librosa.display
from azure.storage.blob import BlobServiceClient


def download_blob(connection_str, container_name, blob_name, download_path):
    """
    Azure Blob에서 지정 파일을 로컬로 다운로드
    """
    blob_service_client = BlobServiceClient.from_connection_string(connection_str)
    blob_client = blob_service_client.get_blob_client(container=container_name, blob = blob_name )
    with open(download_path, "wb") as f:
        data = blob_client.download_blob()
        f.write(data.readall())

def upload_blob(connection_str, container_name, file_path, blob_name):
    """
    로컬에 저장된 파일을 Azure Blob으로 업로드
    """
    blob_service_client = BlobServiceClient.from_connection_string(connection_str)
    blob_client = blob_service_client.get_blob_client(container= container_name, blob = blob_name)
    with open(file_path, "rb") as data:
        blob_client.upload_blob(data, overwrite=True)

