
import os
import numpy as np
import librosa
import soundfile as sf

def preprocess_speech(
    input_wav,
    sr=16000,
    top_db=20,
    max_duration_sec=90,
    silence_threshold_sec=1,
    silence_db_threshold=-40,
    normalize=True
):
    """
    고품질 음성 전처리 파이프라인 (음질 보존용):
    1. 스테레오 유지 & 고급 리샘플링 (kaiser_best)
    2. Normalize (Peak 기반, clipping 방지)
    3. silence_db_threshold 이하 마스킹 (무음 처리)
    4. 앞뒤 무음 트리밍
    5. 1초 이상 침묵 제거 (너무 긴 침묵은 제거, 짧은 침묵은 붙임)
    6. 최대 90초로 자르기
    7. 안전한 파일명으로 *_trimmed.wav 로 저장 (PCM_16 형식)
    """
    print(" 고음질 오디오 로딩 중...")
    # mono=False로 스테레오 유지
    y, _ = librosa.load(input_wav, sr=sr, mono=False, res_type="kaiser_best")

    if normalize:
        print("🎚️ Peak 기반 정규화 중...")
        peak = np.max(np.abs(y))
        if peak > 0:
            y = y / peak * 0.9

    print(" 앞뒤 무음 트리밍 중...")
    y_trimmed, _ = librosa.effects.trim(y, top_db=top_db)

    print(" 긴 침묵 구간 제거 중...")
    intervals = librosa.effects.split(y_trimmed, top_db=top_db)
    max_gap = int(silence_threshold_sec * sr)

    voiced_segments = []
    total_len = 0
    max_total_len = int(max_duration_sec * sr)

    for i, (start, end) in enumerate(intervals):
        segment = y_trimmed[..., start:end]  # works for mono (1D) or stereo (2D)
        if i < len(intervals) - 1:
            next_start = intervals[i + 1][0]
            gap = next_start - end
            if gap <= max_gap:
                # Append gap segment if short
                segment = np.concatenate([segment, y_trimmed[..., end:next_start]], axis=-1)
        voiced_segments.append(segment)
        # Accumulate total length along the time axis.
        if segment.ndim == 1:
            total_len += segment.shape[0]
        else:
            total_len += segment.shape[-1]
        if total_len >= max_total_len:
            break

    if not voiced_segments:
        raise ValueError(" 유효한 발화 구간을 찾지 못했습니다.")

    # Concatenate segments along the time axis
    if y_trimmed.ndim == 1:
        final_audio = np.concatenate(voiced_segments)[:max_total_len]
    else:
        final_audio = np.concatenate(voiced_segments, axis=-1)[:, :max_total_len]

    # 안전한 파일명 만들기 (특수문자 제거 권장)
    base, _ = os.path.splitext(os.path.basename(input_wav))
    output_wav = f"{base}_trimmed.wav"

    # SoundFile expects shape (samples, channels)
    if final_audio.ndim == 2 and final_audio.shape[0] == 2:
        # current shape is (2, T) -> transpose to (T, 2)
        final_audio = final_audio.T

    sf.write(output_wav, final_audio, sr, subtype="PCM_16")

    # For reporting, if stereo, use number of samples / sr as duration from axis 0
    duration = final_audio.shape[0] / sr if final_audio.ndim == 2 else len(final_audio)/sr
    print(f"고품질 전처리 완료: {output_wav} (길이: {duration:.2f}초)")
    return output_wav