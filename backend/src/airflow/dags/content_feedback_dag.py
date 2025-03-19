from datetime import timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from sensors.blob_txt_sensor import AzureBlobTxtSensor
from tasks.blob_tasks import download_blob, upload_blob
from tasks.content_feedback import run_feedback_flow
from dotenv import load_dotenv
import os
import json

load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

# 환경 변수 설정
AZURE_CONN_STR = os.getenv('AZURE_CONN_STR')
REFINED_CONTAINER = os.getenv("REFINED_CONTAINER", "silver_refined")
FEEDBACK_CONTAINER = os.getenv("CONTENT_FEEDBACK_CONTAINER", "gold_content")

# 환경 변수 로드 확인
if not AZURE_CONN_STR or REFINED_CONTAINER or FEEDBACK_CONTAINER:
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
    'content_feedback',  # DAG 이름
    default_args=default_args,  # 설정 넣기
    schedule_interval='* * * * *',  # CRON 표현식으로 매분 실행
    catchup=False,  # 시작일 이후 모든 주기를 실행하지 않음
    max_active_runs=1  # 동시에 실행 가능한 DAG 인스턴스 수
)

# Python Operator에서 호출할 실제 작업 함수.
def process_refined_chunks(**context):
    """
    센서로 확인한 refined 파일에 대해:
    1. REFINED CONTAINER에서 다운로드
    2. 피드백 생성
    3. 피드백을 FEEDBACK CONTAINER로 업로드
    4. 로컬 삭제함
    """
    # Task Instance 가져오기 (Xcom 데이터 접근 위해)
    ti = context['ti']
    # 'check_new_refined_files' 센서 태스크에서 푸시된 refined 파일 목록 가져오기
    new_files = ti.xcom_pull(key='new_refined_files', task_ids='check_new_refined_files')
    # 새파일 없으면 함수 종료
    if not new_files:
        return
    for blob_name in new_files:
        # 1. Refined Blob에서 refined 파일 다운로드
        download_path = f"/tmp/{blob_name}"
        download_blob(AZURE_CONN_STR, REFINED_CONTAINER, blob_name, download_path)

        # 2. 피드백 생성
        with open(download_path, 'r') as f:
            refined_chunks = json.load(f)
        feedback_text = run_feedback_flow(refined_chunks)
        feedback_path = download_path.replace(".json", "_feedback.txt")

        with open(feedback_path, 'w') as f:
            f.write(feedback_text)

        # 3. Feedback Blob에 업로드
        upload_blob(AZURE_CONN_STR, FEEDBACK_CONTAINER, feedback_path, blob_name.replace(".json", "_feedback.txt"))

        os.remove(download_path)
        os.remove(feedback_path)

def set_pitch_purpose(**context):
    """
    pitch_purpose를 설정하고 XCom에 저장
    """
    pitch_purpose = "보안을 위한 코파일럿 사용"
    context['ti'].xcom_push(key='pitch_purpose', value=pitch_purpose)

def print_feedback(**context):
    """
    피드백을 출력
    """
    ti = context['ti']
    feedback = ti.xcom_pull(task_ids='process_files', key='feedback')
    print("\n\n\nContent Feedback Based on MSLearn:", feedback)

check_new_refined_files = AzureBlobTxtSensor(
    task_id="check_new_refined_files",
    connection_str=AZURE_CONN_STR,
    container_name=REFINED_CONTAINER,
    poke_interval=60,
    timeout=60,
    dag=dag
)

process_files = PythonOperator(
    task_id='process_files',
    python_callable=process_refined_chunks,
    provide_context=True,
    dag=dag
)

set_pitch_purpose_task = PythonOperator(
    task_id='set_pitch_purpose',
    python_callable=set_pitch_purpose,
    provide_context=True,
    dag=dag
)

print_feedback_task = PythonOperator(
    task_id='print_feedback',
    python_callable=print_feedback,
    provide_context=True,
    dag=dag
)

# Task flow 설정
check_new_refined_files >> set_pitch_purpose_task >> process_files >> print_feedback_task
