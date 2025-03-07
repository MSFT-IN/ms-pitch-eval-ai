import librosa
import librosa.display
import numpy as np
import matplotlib.pyplot as plt

import librosa
import librosa.display
import numpy as np
import matplotlib.pyplot as plt

def convert_mp3_to_spectrogram(mp3_path, spectrogram_path):
    """
    mp3 파일을 로드하여 Mel-spectrogram으로 변환하고 이미지를 저장
    """
    # 오디오 로드
    y, sr = librosa.load(mp3_path)

    # Mel-spectrogram 생성
    S = librosa.feature.melspectrogram(y=y, sr=sr)
    S_dB = librosa.power_to_db(S, ref=np.max)

    # 스펙트로그램 시각화 설정 
    plt.figure(figsize=(10, 4))
    plt.axis('off')  # 축 제거

    # Mel-spectrogram 표시
    librosa.display.specshow(S_dB, sr=sr, x_axis=None, y_axis=None, cmap='gray')

    # 이미지 저장 
    plt.savefig(spectrogram_path, bbox_inches='tight', pad_inches=0, transparent=True)
    plt.close()
