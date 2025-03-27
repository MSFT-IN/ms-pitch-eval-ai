import os
import numpy as np
from azure.storage.blob import BlobServiceClient
import os
import time

def download_blob(connection_str, container_name, blob_name, download_path):
    """
    Azure Blob에서 지정 파일을 로컬로 다운로드 (다운로드 완료 보장 포함)
    """
    from azure.core.exceptions import ResourceNotFoundError, AzureError

    blob_service_client = BlobServiceClient.from_connection_string(connection_str)
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)

    try:
        data = blob_client.download_blob()
        content = data.readall()

        if not content:
            raise ValueError(f"[ERROR] 다운로드된 blob 내용이 비어 있음: {blob_name}")

        with open(download_path, "wb") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())  # 디스크에 완전히 쓰기 완료 보장

        # 쓰기 완료됐는지 최종 확인 + 대기 (최대 5초)
        for _ in range(5):
            if os.path.exists(download_path) and os.path.getsize(download_path) > 0:
                break
            time.sleep(1)
        else:
            raise RuntimeError(f"[ERROR] 파일 저장 확인 실패: {download_path}")

    except ResourceNotFoundError:
        raise FileNotFoundError(f"[ERROR] Blob이 존재하지 않음: {blob_name}")
    except AzureError as e:
        raise RuntimeError(f"[ERROR] Azure Blob 다운로드 중 실패: {e}")
    except Exception as e:
        raise RuntimeError(f"[ERROR] 알 수 없는 다운로드 실패: {e}")


def upload_blob(connection_str, container_name, file_path, blob_name):
    """
    로컬에 저장된 파일을 Azure Blob으로 업로드
    """
    blob_service_client = BlobServiceClient.from_connection_string(connection_str)
    blob_client = blob_service_client.get_blob_client(container= container_name, blob = blob_name)
    with open(file_path, "rb") as data:
        blob_client.upload_blob(data, overwrite=True)

