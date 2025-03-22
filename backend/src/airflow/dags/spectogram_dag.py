from datetime import timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from sensors.blob_wav_sensor import AzureBlobWavSensor
from tasks.blob_tasks import download_blob, upload_blob
from tasks.tranform_tasks import convert_mp3_to_spectrogram 
from dotenv import load_dotenv
import os


load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

# 환경 변수 설정
AZURE_CONN_STR = os.getenv('AZURE_CONN_STR')
MP3_CONTAINER = os.getenv("AZURE_MP3_CONTAINER", "bronze")
SPECTO_CONTAINER = os.getenv("AZURE_SILVER_CONTAINER", "silver")



print("🔍 환경 변수 확인:")
print("AZURE_CONN_STR:", AZURE_CONN_STR)
print("MP3_CONTAINER:", MP3_CONTAINER)
print("SPECTO_CONTAINER:", SPECTO_CONTAINER)

if not AZURE_CONN_STR:
    raise ValueError("AZURE_CONN_STR가 누락됨 (.env 확인)")


# DAG 기본 설정 (필수임)
default_args = {
    'owner' : 'airflow', # DAG 소유자자
    'depends_on_past' : False, # 이전 DAG 실행 결과 의존 하지않음음
    'start_date' : days_ago(1), # DAG 시작일일
    'retries' : 1, # 실패 재시도 횟수수
    'retry_delay' : timedelta(minutes=1), #재시도 간격 1분 

}


dag = DAG(
    'spectogram_dag', # DAG 이름
    default_args = default_args, # 설정 넣엊귀
    schedule_interval='* * * * *', #CRON 표현식으로 매분 실행
    catchup=False, # 시작일 이후 모든 주기를 실행하지 않음
    max_active_runs =1 # 동시에 실행 가능한 DAG 인스턴스 수 

)

# Python Operator에서 호출할 실제 작업 함수 . 
def process_new_mp3_files(**context):
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
    new_files = ti.xcom_pull(key = 'new_mp3_files', task_ids= 'check_new_mp3_files')
    # 새파일 없으면 함 수 종료료
    if not new_files:
        return
    for blob_name in new_files:

        #1. Bronze BLob에서 mp3다운 
        download_path = f"/tmp/{blob_name}"
        download_blob(AZURE_CONN_STR, MP3_CONTAINER, blob_name, download_path)

        #2. 스펙토그램 이미지로 변환 
        specto_path = download_path.replace(".mp3", ".png")
        convert_mp3_to_spectrogram(download_path, specto_path)

        #3.Silver Blob에 업로드 
        upload_blob(AZURE_CONN_STR, SPECTO_CONTAINER, specto_path, blob_name.replace(".mp3", ".png"))


        os.remove(download_path)
        os.remove(specto_path)



check_new_mp3_files = AzureBlobWavSensor(
    task_id = "check_new_mp3_files",
    connection_str= AZURE_CONN_STR,
    container_name = MP3_CONTAINER,
    poke_interval=60,
    timeout = 60,
    dag = dag
)

process_files = PythonOperator(
    task_id='process_files',
    python_callable=process_new_mp3_files,
    provide_context=True,
    dag=dag

)


# Task flow 설정
check_new_mp3_files >> process_files