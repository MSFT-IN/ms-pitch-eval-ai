from datetime import timedelta
from airflow.utils.dates import days_ago
from airflow.decorators import dag, task
from sensors.blob_wav_sensor import AzureBlobWavSensor
from tasks.blob_tasks import download_blob, upload_blob
from tasks.extract_vocal import demucs_separate_v2
from tasks.pitch_shift import pitch_shift
from tasks.preprocess_speech import preprocess_speech
from tasks.restore_vocal import voicefixer_enhance
from dotenv import load_dotenv
import os

# 환경 변수 로드
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

AZURE_CONN_STR = os.getenv('AZURE_CONN_STR')
WAV_CONTAINER = os.getenv("WAV_CONTAINER", "bronze")
REFINED_CONTAINER = os.getenv("SPECTO_CONTAINER", "silver")

if not AZURE_CONN_STR:
    raise ValueError("AZURE_CONN_STR가 누락됨 (.env 확인)")

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

@dag(
    dag_id='wav_to_refine_dag',
    default_args=default_args,
    schedule_interval='* * * * *',
    catchup=False,
    max_active_runs=1,
)
def wav_to_refine_pipeline():
    # 센서: 새로운 WAV 파일이 있는지 확인 (XCom에 파일 목록 푸시)
    check_new_wav_files = AzureBlobWavSensor(
        task_id="check_new_wav_files",
        connection_str=AZURE_CONN_STR,
        container_name=WAV_CONTAINER,
        poke_interval=60,
        timeout=60,
    )

    @task
    def get_new_files(**context):
        # 센서 태스크에서 XCom으로 전달한 새로운 파일 목록을 받아옴
        ti = context["ti"]
        new_files = ti.xcom_pull(key="new_wav_files", task_ids="check_new_wav_files")
        # 새 파일이 없으면 빈 리스트 반환
        return new_files if new_files else []

    @task
    def process_one_file(blob_name: str):
        # 1. Bronze Blob에서 파일 다운로드
        download_path = f"/tmp/{blob_name}"
        download_blob(AZURE_CONN_STR, WAV_CONTAINER, blob_name, download_path)

        # 2. Speech Data 전처리 (1)
        output_preprocess = preprocess_speech(download_path)

        # 3. WAV에서 목소리 추출
        output_vocal = demucs_separate_v2(output_preprocess)

        # 4. Speech Data 전처리 (2) - normalization 없이
        output_preprocess_2 = preprocess_speech(output_vocal, normalize=False)

        # 5. Pitch 정규화
        output_pitch_shift = pitch_shift(output_preprocess_2)

        # 6. 복원한 가상 목소리 생성
        output_restore = voicefixer_enhance(output_pitch_shift)

        # 7. Speech Data 전처리 (3) - normalization 없이
        output_final = preprocess_speech(output_restore, normalize=False)

        # 8. 애저 Blob에 업로드 (파일명은 전체 경로에서 추출)
        filename = os.path.basename(output_final)
        upload_blob(AZURE_CONN_STR, REFINED_CONTAINER, output_final, filename)

        # 9. 처리 후 로컬 임시 파일 삭제
        for path in [output_final, output_preprocess, output_preprocess_2,
                     output_vocal, output_pitch_shift, download_path, output_restore]:
            if os.path.exists(path):
                os.remove(path)
                
        return f"Processed {blob_name}"

    # 센서 태스크를 먼저 실행하도록 의존성 설정
    new_files = get_new_files()
    # new_files 리스트의 각 요소마다 process_one_file 태스크를 병렬로 실행
    processed_results = process_one_file.expand(blob_name=new_files)

    # (원한다면 processed_results 결과를 로그로 확인할 수 있음)

dag_instance = wav_to_refine_pipeline()
