import os
import torchaudio
import torch
from demucs.pretrained import get_model
from demucs.apply import apply_model

print("Demucs 모델 로드 중...")
model = get_model('htdemucs')

def demucs_separate_v2(input_wav, output_dir="."):
    """
    Demucs 모델로 목소리만 추출해서 저장 (기본: 현재 경로)
    output 파일: <입력파일명>_vocal.wav
    """
    print("오디오 로딩 중...")
    mixture, sr = torchaudio.load(input_wav)

    x = mixture.unsqueeze(0).float()  # Demucs는 float32 입력 필요

    if sr != model.samplerate:
        print(f"샘플레이트 {sr} → {model.samplerate}로 리샘플링 중...")
        resample = torchaudio.transforms.Resample(orig_freq=sr, new_freq=model.samplerate)
        x = resample(x)
        sr = model.samplerate

    print(" Demucs 분리 중 (apply_model)...")
    out = apply_model(model, x)[0]  # [sources, channels, time]
    vocal = out[model.sources.index("vocals")]

    # 출력 경로: 원본 이름 + "_vocal.wav"
    base = os.path.splitext(os.path.basename(input_wav))[0]
    vocal_path = os.path.join(output_dir, f"{base}_vocal.wav")

    print(f"보컬만 저장 중 → {vocal_path}")
    torchaudio.save(vocal_path, vocal, sr)

    print(f"완료: {vocal_path}")
    return vocal_path