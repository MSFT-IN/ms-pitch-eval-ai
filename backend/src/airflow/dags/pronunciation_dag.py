from datetime import timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from sensors.blob_wav_sensor import AzureBlobWavSensor
from tasks.blob_tasks import download_blob, upload_blob
from tasks.continuous_recognition import extract_data_from_airflow 
from dotenv import load_dotenv
import os
import json

load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

# set env
AZURE_CONN_STR = os.getenv('AZURE_CONN_STR')
WAV_CONTAINER = os.getenv("WAV_CONTAINER")
PRONUNCIATION_CONTAINER = os.getenv("PRONUNCIATION_CONTAINER")

# check env
if not (AZURE_CONN_STR or WAV_CONTAINER or PRONUNCIATION_CONTAINER):
    raise ValueError("Azure Container Not Found")

# set DAG
default_args = {
    'owner' : 'airflow', # DAG owner
    'depends_on_past' : False, 
    'start_date' : days_ago(1), 
    'retries' : 1, 
    'retry_delay' : timedelta(minutes=1),
}

dag = DAG(
    'extract_pronunciation_data', # name of DAG
    default_args = default_args, # default setting
    schedule_interval='* * * * *', # every minute
    catchup=False, 
    max_active_runs = 1 
)

def process_new_wav_files(**context):
    # get Task Instance (to collect blob names in XCom)
    ti = context['ti']
    new_files = ti.xcom_pull(key = 'new_wav_files', task_ids= 'check_new_wav_files') # new_files: newly uploaded wav file names

    if not new_files:
        return

    for blob_name in new_files:
        #1. Download wav files from Bronze Blob
        download_path = f"/tmp/{blob_name}"
        download_blob(AZURE_CONN_STR, WAV_CONTAINER, blob_name, download_path)

        #2. extract pronunciation data from blob
        airflow_json_path = extract_data_from_airflow(download_path)

        #3.Upload json to Silver Blob
        upload_blob(AZURE_CONN_STR, PRONUNCIATION_CONTAINER, airflow_json_path, blob_name.replace(".wav", "_pronunciation.json"))

        # Remove local files
        os.remove(download_path)
        os.remove(airflow_json_path)

# set Azure Blob Sensor
check_new_wav_files = AzureBlobWavSensor(
    task_id="check_new_wav_files",
    connection_str=AZURE_CONN_STR,
    container_name=WAV_CONTAINER,
    poke_interval=60,
    timeout=60,
    dag=dag
)

# set Python Operator
process_files = PythonOperator(
    task_id='process_files',
    python_callable=process_new_wav_files,
    provide_context=True,
    dag=dag
)

# set Task Flow
check_new_wav_files >> process_files