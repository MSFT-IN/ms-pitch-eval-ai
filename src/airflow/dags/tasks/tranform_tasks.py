import librosa
import librosa.display
import numpy as np
import matplotlib.pyplot as plt

def convert_mp3_to_spectrogram(mp3_path, spectrogram_base_path, segment_duration=10):
    """
    mp3 파일을 10초 단위로 자르고, 각 구간을 Mel-spectrogram으로 변환 후 이미지 파일로 저장.

    Args:
        mp3_path (str): 입력 MP3 파일 경로.
        spectrogram_base_path (str): 저장할 스펙트로그램 이미지의 경로 (확장자 제외).
        segment_duration (int): 자를 오디오 길이 (초 단위, 기본값: 10초).
    """
    # 오디오 로드
    y, sr = librosa.load(mp3_path)
    total_duration = librosa.get_duration(y=y, sr=sr)

    # 10초 단위로 오디오 잘라서 Mel-spectrogram 생성
    num_segments = int(np.ceil(total_duration / segment_duration))

    for i in range(num_segments):
        start_sample = i * segment_duration * sr
        end_sample = min((i + 1) * segment_duration * sr, len(y))

        # 오디오 구간 추출
        y_segment = y[int(start_sample):int(end_sample)]

        # Mel-spectrogram 생성
        S = librosa.feature.melspectrogram(y=y_segment, sr=sr)
        S_dB = librosa.power_to_db(S, ref=np.max)

        # 스펙트로그램 시각화
        plt.figure(figsize=(10, 4))
        plt.axis('off')
        librosa.display.specshow(S_dB, sr=sr, cmap='gray')

        # 이미지 파일 이름 생성 (_1, _2 형식)
        segment_filename = f"{spectrogram_base_path}_{i+1}.png"

        # 이미지 저장 (투명 배경, 여백 없음)
        plt.savefig(segment_filename, bbox_inches='tight', pad_inches=0, transparent=True)
        plt.close()

        print(f"Saved: {segment_filename}")
        
    return num_segments