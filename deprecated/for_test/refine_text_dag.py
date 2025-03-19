from datetime import timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from sensors.blob_json_sensor import AzureBlobJsonSensor
from tasks.blob_tasks import download_blob, upload_blob
from dotenv import load_dotenv
import os
from tasks.run_stt import refine_stt
import json

load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

# 환경 변수 설정
AZURE_CONN_STR = os.getenv('AZURE_CONN_STR')
STT_CONTAINER = os.getenv("STT_CONTAINER", "silver")
REFINED_CONTAINER = os.getenv("REFINED_CONTAINER", "silver_refined")

# 환경 변수 로드 확인
if not AZURE_CONN_STR or STT_CONTAINER or REFINED_CONTAINER:
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
    'stt_refinement',  # DAG 이름
    default_args=default_args,  # 설정 넣기
    schedule_interval='* * * * *',  # CRON 표현식으로 매분 실행
    catchup=False,  # 시작일 이후 모든 주기를 실행하지 않음
    max_active_runs=1  # 동시에 실행 가능한 DAG 인스턴스 수
)

# Python Operator에서 호출할 실제 작업 함수.
def process_new_txt_files(**context):
    """
    센서로 확인한 txt 파일에 대해:
    1. STT CONTAINER에서 다운로드
    2. 텍스트 정제
    3. 정제된 텍스트를 REFINED CONTAINER로 업로드
    4. 로컬 삭제함
    """
    # Task Instance 가져오기 (Xcom 데이터 접근 위해)
    ti = context['ti']
    # 'check_new_txt_files' 센서 태스크에서 푸시된 txt 파일 목록 가져오기
    new_files = ti.xcom_pull(key='new_txt_files', task_ids='check_new_txt_files')
    # 새파일 없으면 함수 종료
    if not new_files:
        return
    for blob_name in new_files:
        # 1. Silver Blob에서 txt 다운로드
        download_path = f"/tmp/{blob_name}"
        download_blob(AZURE_CONN_STR, STT_CONTAINER, blob_name, download_path)

        # 2. 텍스트 정제
        with open(download_path, 'r') as f:
            recognized_chunks = json.load(f)
        pitch_purpose = "피치 목적"  # 피치 목적 설정
        refined_text, refined_chunks = refine_stt(pitch_purpose, recognized_chunks)
        refined_path = download_path.replace(".json", "_refined.txt")
        refined_chunks_path = download_path.replace(".json", "_refined_chunks.json")

        with open(refined_path, 'w') as f:
            f.write(refined_text)

        with open(refined_chunks_path, 'w') as f:
            json.dump(refined_chunks, f)

        # 3. Refined Blob에 업로드
        upload_blob(AZURE_CONN_STR, REFINED_CONTAINER, refined_path, blob_name.replace(".json", "_refined.txt"))
        upload_blob(AZURE_CONN_STR, REFINED_CONTAINER, refined_chunks_path, blob_name.replace(".json", "_refined_chunks.json"))

        os.remove(download_path)
        os.remove(refined_path)
        os.remove(refined_chunks_path)

checjsonew_txt_files = AzureBlobJsonSensor(
    task_id="check_new_json_files",
    connection_str=AZURE_CONN_STR,
    container_name=STT_CONTAINER,
    poke_interval=60,
    timeout=60,
    dag=dag
)

process_files = PythonOperator(
    task_id='process_files',
    python_callable=process_new_txt_files,
    provide_context=True,
    dag=dag
)

# Task flow 설정
check_new_json_files >> process_files
