from datetime import timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from sensors.blob_wav_sensor import AzureBlobWavSensor
from tasks.blob_tasks import download_blob, upload_blob
from dotenv import load_dotenv
import os
from tasks.run_stt import run_basic_stt
import json

load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

# 환경 변수 설정
AZURE_CONN_STR = os.getenv('AZURE_CONN_STR')
WAV_CONTAINER = os.getenv("AZURE_WAV_CONTAINER", "bronze")
STT_CONTAINER = os.getenv("AZURE_STT_CONTAINER", "silver")

# 환경 변수 로드 확인
if not AZURE_CONN_STR or WAV_CONTAINER or STT_CONTAINER:
    raise ValueError("AZURE_CONN_STR not found")

# DAG 기본 설정 (필수임)
default_args = {
    'owner': 'airflow',  # DAG 소유자
    'depends_on_past': False,  # 이전 DAG 실행 결과 의존 하지않음
    'start_date': days_ago(1),  # DAG 시작일
    'retries': 1,  # 실패 재시도 횟수
    'retry_delay': timedelta(minutes=1),  # 재시도 간격 1분
}

dag = DAG(
    'wav_to_stt',  # DAG 이름
    default_args=default_args,  # 설정 넣기
    schedule_interval='* * * * *',  # CRON 표현식으로 매분 실행
    catchup=False,  # 시작일 이후 모든 주기를 실행하지 않음
    max_active_runs=1  # 동시에 실행 가능한 DAG 인스턴스 수
)

# Python Operator에서 호출할 실제 작업 함수.
def process_new_wav_files(**context):
    """
    센서로 확인한 wav 파일에 대해:
    1. WAV CONTAINER에서 다운로드
    2. STT 변환
    3. STT CONTAINER로 업로드
    4. 로컬 삭제함
    """
    # Task Instance 가져오기 (Xcom 데이터 접근 위해)
    ti = context['ti']
    # 'check_new_wav_files' 센서 태스크에서 푸시된 wav 파일 목록 가져오기
    new_files = ti.xcom_pull(key='new_wav_files', task_ids='check_new_wav_files')
    # 새파일 없으면 함수 종료
    if not new_files:
        return
    for blob_name in new_files:
        # 1. Bronze Blob에서 wav 다운로드
        download_path = f"/tmp/{blob_name}"
        download_blob(AZURE_CONN_STR, WAV_CONTAINER, blob_name, download_path)

        # 2. STT 변환
        stt_text, recognized_chunks = run_basic_stt(download_path)
        stt_text_path = download_path.replace(".wav", ".txt")
        stt_chunks_path = download_path.replace(".wav", "_chunks.json")

        with open(stt_text_path, 'w') as f:
            f.write(stt_text)

        with open(stt_chunks_path, 'w') as f:
            json.dump(recognized_chunks, f)

        # 3. Silver Blob에 업로드
        upload_blob(AZURE_CONN_STR, STT_CONTAINER, stt_text_path, blob_name.replace(".wav", "_stt.txt"))
        upload_blob(AZURE_CONN_STR, STT_CONTAINER, stt_chunks_path, blob_name.replace(".wav", "_stt_chunks.json"))

        os.remove(download_path)
        os.remove(stt_text_path)
        os.remove(stt_chunks_path)

check_new_wav_files = AzureBlobWavSensor(
    task_id="check_new_wav_files",
    connection_str=AZURE_CONN_STR,
    container_name=WAV_CONTAINER,
    poke_interval=60,
    timeout=60,
    dag=dag
)

process_files = PythonOperator(
    task_id='process_files',
    python_callable=process_new_wav_files,
    provide_context=True,
    dag=dag
)

# Task flow 설정
check_new_wav_files >> process_files
