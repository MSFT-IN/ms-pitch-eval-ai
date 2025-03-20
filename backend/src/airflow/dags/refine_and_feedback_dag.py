from datetime import timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from sensors.blob_json_sensor import AzureBlobJsonSensor
from tasks.blob_tasks import download_blob, upload_blob
from tasks.run_stt import refine_stt
from backend.src.airflow.dags.tasks.generate_content_feedback import generate_content_feedback
from dotenv import load_dotenv
import os
import json
from backend.src.airflow.dags.tasks.generate_pitch_purpose import get_pitch_purpose

load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

# 환경 변수 설정
AZURE_CONN_STR = os.getenv('AZURE_CONN_STR')
STT_CONTAINER = os.getenv("STT_CONTAINER", "silver")
FEEDBACK_CONTAINER = os.getenv("CONTENT_FEEDBACK_CONTAINER", "gold_content")

# 환경 변수 로드 확인
if not AZURE_CONN_STR or STT_CONTAINER or FEEDBACK_CONTAINER:
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
    'refine_and_feedback',  # DAG 이름
    default_args=default_args,  # 설정 넣기
    schedule_interval='* * * * *',  # CRON 표현식으로 매분 실행
    catchup=False,  # 시작일 이후 모든 주기를 실행하지 않음
    max_active_runs=1  # 동시에 실행 가능한 DAG 인스턴스 수
)

# Python Operator에서 호출할 실제 작업 함수.
def process_new_json_files(**context):
    """
    센서로 확인한 json 파일에 대해:
    1. STT CONTAINER에서 다운로드
    2. 텍스트 정제
    3. 피드백 생성
    4. 정제된 텍스트와 피드백을 FEEDBACK CONTAINER로 업로드
    5. 로컬 삭제함
    """
    # Task Instance 가져오기 (Xcom 데이터 접근 위해)
    ti = context['ti']
    # 'check_new_json_files' 센서 태스크에서 푸시된 json 파일 목록 가져오기
    new_files = ti.xcom_pull(key='new_json_files', task_ids='check_new_json_files')
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
        
        # 피치 목적 판단
        pitch_purpose = get_pitch_purpose(recognized_chunks)
        
        # STT 퀄리티 향상
        refined_text, refined_chunks = refine_stt(pitch_purpose, recognized_chunks)
        refined_chunks_path = download_path.replace(".json", "_refined_chunks.json")

        with open(refined_chunks_path, 'w') as f:
            json.dump(refined_chunks, f)

        # 3. 피드백 생성
        feedback_text = generate_content_feedback(pitch_purpose, refined_chunks)
        combined_text = "[AI Speech Transcription]\n" + refined_text + "\n\n[AI Assisted Feedback]\n" + feedback_text + "\n\n"
        combined_path = download_path.replace(".json", "_feedback.txt")

        with open(combined_path, 'w') as f:
            f.write(combined_text)

        # 4. Feedback Blob에 업로드
        upload_blob(AZURE_CONN_STR, FEEDBACK_CONTAINER, combined_path, blob_name.replace(".json", "_feedback.txt"))

        os.remove(download_path)
        os.remove(refined_chunks_path)
        os.remove(combined_path)

check_new_json_files = AzureBlobJsonSensor(
    task_id="check_new_json_files",
    connection_str=AZURE_CONN_STR,
    container_name=STT_CONTAINER,
    keyword="stt",  # Add keyword parameter
    poke_interval=60,
    timeout=60,
    dag=dag
)

process_files = PythonOperator(
    task_id='process_files',
    python_callable=process_new_json_files,
    provide_context=True,
    dag=dag
)

# Task flow 설정
check_new_json_files >> process_files
