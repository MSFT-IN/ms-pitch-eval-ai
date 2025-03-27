from datetime import timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from sensors.blob_wav_sensor import AzureBlobWavSensor
from tasks.score_paralingual import extract_speech_features_robust
from tasks.blob_tasks import download_blob, upload_blob
from dotenv import load_dotenv
import os


load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))


# 환경 변수 설정
AZURE_CONN_STR = os.getenv('AZURE_CONN_STR')
REFINED_CONTAINER = os.getenv("REFINED_CONTAINER", "silver")
PA_CONTAINER = os.getenv("PARALINGUAL_ANALYSIS_CONTAINER", "gold")


print("🔍 환경 변수 확인:")
print("AZURE_CONN_STR:", AZURE_CONN_STR)
print("REFINED_CONTAINER:", REFINED_CONTAINER)
print("PA_CONTAINER:", PA_CONTAINER)


if not (AZURE_CONN_STR and REFINED_CONTAINER and PA_CONTAINER):
    raise ValueError("인젝션 에러")


# DAG 기본 설정 (필수임)
default_args = {
    'owner' : 'airflow', # DAG 소유자자
    'depends_on_past' : False, # 이전 DAG 실행 결과 의존 하지않음음
    'start_date' : days_ago(1), # DAG 시작일
    'retries' : 1, # 실패 재시도 횟수수
    'retry_delay' : timedelta(minutes=1), #재시도 간격 1분 
}


dag = DAG(
    'score_paralinguistic_features', # DAG 이름
    default_args = default_args, # 설정 넣엊귀
    schedule_interval='* * * * *', # CRON 표현식으로 매분 실행
    catchup=False, # 시작일 이후 모든 주기를 실행하지 않음
    max_active_runs = 1 # 동시에 실행 가능한 DAG 인스턴스 수 
)


# Python Operator에서 호출할 실제 작업 함수 . 
def score_paraling(**context):
    """
    센서로 확인한 mp3파일에 대해:
    1. MP3 CONTAINER에서 다운로드
    2. 스펙토그램으로 변환
    3. SPECTO CONTAINER로 업로드 
    4. 로컬 삭제함
    """
    # Task Instance rkwudhrl (Xcom 데이터 접근 위해)
    ti = context['ti']
    # 'check_new_mp3_files' 센서 태스크에서 푸시된 mp3 파일 목록 가져오기
    new_files = ti.xcom_pull(key = 'new_wav_files', task_ids= 'check_new_wav_files')
    # 새파일 없으면 함수 종료
    
    if not new_files:
        return
    for blob_name in new_files:
        
        #1. Blob에서 wav파일 다운로드         
        download_path = f"/tmp/{blob_name}"
        download_blob(AZURE_CONN_STR, REFINED_CONTAINER, blob_name, download_path)
        
        #2. output 추출
        extract_speech_features_robust(download_path)
        json_path = os.path.splitext(download_path)[0] + "_features.json"
        
        #3.Gold Blob에 업로드 
        upload_blob(AZURE_CONN_STR, PA_CONTAINER, json_path, blob_name.replace(".wav", ".json"))
        os.remove(download_path)
        os.remove(json_path)


check_new_mp3_files = AzureBlobWavSensor(
    task_id = "check_new_wav_files",
    connection_str= AZURE_CONN_STR,
    container_name = REFINED_CONTAINER,
    poke_interval=60,
    timeout = 60,
    dag = dag
)

score_paralinguistic_features = PythonOperator(
    task_id='score_paralinguistic_features',
    python_callable=score_paraling,
    provide_context=True,
    dag=dag

)

# Task flow 설정
check_new_mp3_files >> score_paralinguistic_features