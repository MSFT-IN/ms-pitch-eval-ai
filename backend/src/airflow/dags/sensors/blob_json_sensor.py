from airflow.sensors.base import BaseSensorOperator
from airflow.utils.decorators import apply_defaults
from azure.storage.blob import BlobServiceClient
from datetime import datetime, timedelta, timezone

class AzureBlobJsonSensor(BaseSensorOperator):
    """
    Azure Blob Storage의 지정 컨테이너에서 최근 1분내 생성된 json파일이 있는지 체크!
    파일이 존재하면, XCom으로 목록 넘겨주기 
    """
    @apply_defaults
    def __init__(self, connection_str, container_name, keyword=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connection_str = connection_str
        self.container_name = container_name
        self.keyword = keyword

    def poke(self, context):
        self.log.info("Checking for new json files in container %s", self.container_name)
        blob_service_client = BlobServiceClient.from_connection_string(self.connection_str)
        container_client = blob_service_client.get_container_client(self.container_name)
        blobs = container_client.list_blobs()
        new_files = []
        now = datetime.now(timezone.utc)

        for blob in blobs: 
            if blob.name.endswith(".json"):
                if self.keyword and self.keyword not in blob.name:
                    continue
                if blob.last_modified >= now - timedelta(minutes=1):
                    new_files.append(blob.name)

        if new_files: 
            context['ti'].xcom_push(key='new_json_files', value = new_files)
            self.log.info("Found new json files: %s", new_files)
            return True
        else: 
            self.log.info("No new json files found.")
            return False
