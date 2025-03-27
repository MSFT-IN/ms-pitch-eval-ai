# import numpy as np
# import librosa
# import parselmouth
# import pyworld as pw
# import soundfile as sf
# from scipy.signal import find_peaks, medfilt
# import os
# import json

# def extract_speech_features_robust(wav_path, sr=16000, top_db=20, save_json=True):
#     """
#     Extract robust speech features from a WAV file using Python-only methods
#     and optionally save them to a JSON file.

#     Features extracted:
#       - pitch_range: Robust pitch range (Hz) using pyworld with normalization & percentile filtering
#       - loudness_std: Standard deviation of dB-scaled STFT magnitudes (after removing extreme outliers)
#       - pause_ratio: Proportion of silence using librosa.effects.split on a smoothed signal
#       - speech_rate: Approximate syllables/sec estimated from RMS energy peaks (after smoothing)
#       - jitter: Local jitter (%) using parselmouth (Praat)
#       - shimmer: Local shimmer (%) using parselmouth (Praat)

#     Args:
#         wav_path (str): Path to the WAV file.
#         sr (int): Sampling rate for processing (default 16000).
#         top_db (int): dB threshold for silence detection (default 20).
#         save_json (bool): Whether to save the features as a JSON file (default True).

#     Returns:
#         dict: Extracted features with robust estimation.
#     """
#     y, _ = librosa.load(wav_path, sr=sr, mono=True, res_type="kaiser_best")

#     # === 1. Loudness Std ===
#     S = np.abs(librosa.stft(y))
#     loudness_db = librosa.amplitude_to_db(S, ref=np.max)
#     dB_flat = loudness_db.flatten()
#     lower_db, upper_db = np.percentile(dB_flat, [5, 95])
#     valid_dB = dB_flat[(dB_flat >= lower_db) & (dB_flat <= upper_db)]
#     loudness_std = np.std(valid_dB)

#     # === 2. Pause Ratio ===
#     y_smooth = medfilt(y, kernel_size=5)
#     intervals = librosa.effects.split(y_smooth, top_db=top_db)
#     total_voiced = sum([end - start for start, end in intervals])
#     pause_ratio = 1 - (total_voiced / len(y))

#     # === 3. Speech Rate ===
#     energy = librosa.feature.rms(y=y)[0]
#     energy_smooth = medfilt(energy, kernel_size=5)
#     height_threshold = 0.2 * np.max(energy_smooth)
#     time_resolution = len(y) / len(energy_smooth)
#     min_distance = int(0.15 * sr / time_resolution)
#     peaks, _ = find_peaks(energy_smooth, height=height_threshold, distance=min_distance)
#     duration_sec = len(y) / sr
#     speech_rate = len(peaks) / duration_sec if duration_sec > 0 else 0

#     # === 4. Pitch Range ===
#     try:
#         _f0, t = pw.harvest(y.astype(np.float64), sr, f0_floor=50.0, f0_ceil=500.0)
#         f0 = _f0[np.isfinite(_f0)]
#         f0 = f0[(f0 > 50) & (f0 < 500)]
#         if len(f0) > 0:
#             median_f0 = np.nanmedian(f0)
#             f0_norm = f0 / median_f0
#             lower, upper = np.percentile(f0_norm, [10, 90])
#             f0_clean = f0_norm[(f0_norm >= lower) & (f0_norm <= upper)]
#             pitch_range_ratio = f0_clean.max() - f0_clean.min() if len(f0_clean) > 0 else 0
#             pitch_range = pitch_range_ratio * median_f0
#         else:
#             pitch_range = 0
#     except Exception as e:
#         print("⚠️ Pitch estimation failed:", e)
#         pitch_range = 0

#     # === 5. Jitter & Shimmer ===
#     try:
#         snd = parselmouth.Sound(wav_path)
#         point_process = parselmouth.praat.call(snd, "To PointProcess (periodic, cc)", 75, 500)
#         jitter = parselmouth.praat.call(point_process, "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3)
#         shimmer = parselmouth.praat.call([snd, point_process], "Get shimmer (local)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
#     except Exception as e:
#         print("⚠️ Jitter/Shimmer estimation failed:", e)
#         jitter = shimmer = 0

#     # 결과 딕셔너리 생성
#     features = {
#         "pitch_range": round(pitch_range, 2),
#         "loudness_std": round(loudness_std, 2),
#         "pause_ratio": round(pause_ratio, 3),
#         "speech_rate": round(speech_rate, 2),
#         "jitter": round(jitter, 4),
#         "shimmer": round(shimmer, 4)
#     }

    
#     # === JSON 저장 ===
#     json_path = None
#     if save_json:
#         json_path = os.path.splitext(wav_path)[0] + "_features.json"
#         try:
#             with open(json_path, "w") as f:
#                 json.dump(features, f, indent=4)
#                 f.flush()  # 버퍼를 OS로
#                 os.fsync(f.fileno())  # OS에서 디스크로
#             print(f"Features saved to {json_path}")
#         except Exception as e:
#             print(f"Failed to save JSON: {e}")
#             json_path = None

#     # features는 항상 리턴, json_path도 리턴 가능하게 하면 좋음
#     return features if not save_json else (features, json_path)

# import numpy as np
# import librosa
# import parselmouth
# import pyworld as pw
# import soundfile as sf
# from scipy.signal import find_peaks, medfilt
# import os
# import json

# def extract_speech_features_robust(wav_path, sr=16000, top_db=20, save_json=True):
#     """
#     Extract robust speech features from a WAV file using Python-only methods
#     and optionally save them to a JSON file.

#     Features extracted:
#       - pitch_range: Robust pitch range (Hz) using pyworld with normalization & percentile filtering
#       - loudness_std: Standard deviation of dB-scaled STFT magnitudes (after removing extreme outliers)
#       - pause_ratio: Proportion of silence using librosa.effects.split on a smoothed signal
#       - speech_rate: Approximate syllables/sec estimated from RMS energy peaks (after smoothing)
#       - jitter: Local jitter (%) using parselmouth (Praat)
#       - shimmer: Local shimmer (%) using parselmouth (Praat)

#     Args:
#         wav_path (str): Path to the WAV file.
#         sr (int): Sampling rate for processing (default 16000).
#         top_db (int): dB threshold for silence detection (default 20).
#         save_json (bool): Whether to save the features as a JSON file (default True).

#     Returns:
#         dict or tuple: Extracted features as a dict. If save_json is True, returns a tuple (features, json_path).
#     """
#     # === Audio Load ===
#     y, _ = librosa.load(wav_path, sr=sr, mono=True, res_type="kaiser_best")

#     # === 1. Loudness Std ===
#     S = np.abs(librosa.stft(y))
#     loudness_db = librosa.amplitude_to_db(S, ref=np.max)
#     dB_flat = loudness_db.flatten()
#     lower_db, upper_db = np.percentile(dB_flat, [5, 95])
#     valid_dB = dB_flat[(dB_flat >= lower_db) & (dB_flat <= upper_db)]
#     loudness_std = np.std(valid_dB)

#     # === 2. Pause Ratio ===
#     y_smooth = medfilt(y, kernel_size=5)
#     intervals = librosa.effects.split(y_smooth, top_db=top_db)
#     total_voiced = sum([end - start for start, end in intervals])
#     pause_ratio = 1 - (total_voiced / len(y))

#     # === 3. Speech Rate ===
#     energy = librosa.feature.rms(y=y)[0]
#     energy_smooth = medfilt(energy, kernel_size=5)
#     height_threshold = 0.2 * np.max(energy_smooth)
#     time_resolution = len(y) / len(energy_smooth)
#     min_distance = int(0.15 * sr / time_resolution)
#     peaks, _ = find_peaks(energy_smooth, height=height_threshold, distance=min_distance)
#     duration_sec = len(y) / sr
#     speech_rate = len(peaks) / duration_sec if duration_sec > 0 else 0

#     # === 4. Pitch Range ===
#     try:
#         _f0, t = pw.harvest(y.astype(np.float64), sr, f0_floor=50.0, f0_ceil=500.0)
#         f0 = _f0[np.isfinite(_f0)]
#         f0 = f0[(f0 > 50) & (f0 < 500)]
#         if len(f0) > 0:
#             median_f0 = np.nanmedian(f0)
#             f0_norm = f0 / median_f0
#             lower, upper = np.percentile(f0_norm, [10, 90])
#             f0_clean = f0_norm[(f0_norm >= lower) & (f0_norm <= upper)]
#             pitch_range_ratio = f0_clean.max() - f0_clean.min() if len(f0_clean) > 0 else 0
#             pitch_range = pitch_range_ratio * median_f0
#         else:
#             pitch_range = 0
#     except Exception as e:
#         print("⚠️ Pitch estimation failed:", e)
#         pitch_range = 0

#     # === 5. Jitter & Shimmer ===
#     try:
#         snd = parselmouth.Sound(wav_path)
#         point_process = parselmouth.praat.call(snd, "To PointProcess (periodic, cc)", 75, 500)
#         jitter = parselmouth.praat.call(point_process, "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3)
#         shimmer = parselmouth.praat.call([snd, point_process], "Get shimmer (local)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
#     except Exception as e:
#         print("⚠️ Jitter/Shimmer estimation failed:", e)
#         jitter = shimmer = 0

#     # Construct features dictionary
#     features = {
#         "pitch_range": round(pitch_range, 2),
#         "loudness_std": round(loudness_std, 2),
#         "pause_ratio": round(pause_ratio, 3),
#         "speech_rate": round(speech_rate, 2),
#         "jitter": round(jitter, 4),
#         "shimmer": round(shimmer, 4)
#     }

#     # === JSON 저장 ===
#     json_path = None
#     if save_json:
#         json_path = os.path.splitext(wav_path)[0] + "_features.json"
#         try:
#             with open(json_path, "w") as f:
#                 json.dump(features, f, indent=4)
#                 f.flush()                # 버퍼를 강제로 비움
#                 os.fsync(f.fileno())     # OS 레벨에서 디스크에 기록 강제
#             print(f"✅ Features saved to {json_path}")
#         except Exception as e:
#             print(f"❌ Failed to save JSON: {e}")
#             json_path = None

#     if save_json:
#         return features, json_path
#     else:
#         return features
import numpy as np
import librosa
import parselmouth
import pyworld as pw
import soundfile as sf
from scipy.signal import find_peaks, medfilt
import os
import json

def extract_speech_features_robust(wav_path, sr=16000, top_db=20, save_json=True):
    """
    Extract robust speech features from a WAV file using Python-only methods
    and optionally save them to a JSON file.

    Features extracted:
      - pitch_range: Robust pitch range (Hz) using pyworld with normalization & percentile filtering
      - loudness_std: Standard deviation of dB-scaled STFT magnitudes (after removing extreme outliers)
      - pause_ratio: Proportion of silence using librosa.effects.split on a smoothed signal
      - speech_rate: Approximate syllables/sec estimated from RMS energy peaks (after smoothing)
      - jitter: Local jitter (%) using parselmouth (Praat)
      - shimmer: Local shimmer (%) using parselmouth (Praat)

    Args:
        wav_path (str): Path to the WAV file.
        sr (int): Sampling rate for processing (default 16000).
        top_db (int): dB threshold for silence detection (default 20).
        save_json (bool): Whether to save the features as a JSON file (default True).

    Returns:
        dict or tuple: Extracted features as a dict. If save_json is True, returns a tuple (features, json_path).
    """
    # === Audio Load ===
    y, _ = librosa.load(wav_path, sr=sr, mono=True, res_type="kaiser_best")

    # === 1. Loudness Std ===
    S = np.abs(librosa.stft(y))
    loudness_db = librosa.amplitude_to_db(S, ref=np.max)
    dB_flat = loudness_db.flatten()
    lower_db, upper_db = np.percentile(dB_flat, [5, 95])
    valid_dB = dB_flat[(dB_flat >= lower_db) & (dB_flat <= upper_db)]
    loudness_std = np.std(valid_dB)

    # === 2. Pause Ratio ===
    y_smooth = medfilt(y, kernel_size=5)
    intervals = librosa.effects.split(y_smooth, top_db=top_db)
    total_voiced = sum([end - start for start, end in intervals])
    pause_ratio = 1 - (total_voiced / len(y))

    # === 3. Speech Rate ===
    energy = librosa.feature.rms(y=y)[0]
    energy_smooth = medfilt(energy, kernel_size=5)
    height_threshold = 0.2 * np.max(energy_smooth)
    time_resolution = len(y) / len(energy_smooth)
    min_distance = int(0.15 * sr / time_resolution)
    peaks, _ = find_peaks(energy_smooth, height=height_threshold, distance=min_distance)
    duration_sec = len(y) / sr
    speech_rate = len(peaks) / duration_sec if duration_sec > 0 else 0

    # === 4. Pitch Range ===
    try:
        _f0, t = pw.harvest(y.astype(np.float64), sr, f0_floor=50.0, f0_ceil=500.0)
        f0 = _f0[np.isfinite(_f0)]
        f0 = f0[(f0 > 50) & (f0 < 500)]
        if len(f0) > 0:
            median_f0 = np.nanmedian(f0)
            f0_norm = f0 / median_f0
            lower, upper = np.percentile(f0_norm, [10, 90])
            f0_clean = f0_norm[(f0_norm >= lower) & (f0_norm <= upper)]
            pitch_range_ratio = f0_clean.max() - f0_clean.min() if len(f0_clean) > 0 else 0
            pitch_range = pitch_range_ratio * median_f0
        else:
            pitch_range = 0
    except Exception as e:
        print("⚠️ Pitch estimation failed:", e)
        pitch_range = 0

    # === 5. Jitter & Shimmer ===
    try:
        snd = parselmouth.Sound(wav_path)
        point_process = parselmouth.praat.call(snd, "To PointProcess (periodic, cc)", 75, 500)
        jitter = parselmouth.praat.call(point_process, "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3)
        shimmer = parselmouth.praat.call([snd, point_process], "Get shimmer (local)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
    except Exception as e:
        print("⚠️ Jitter/Shimmer estimation failed:", e)
        jitter = shimmer = 0

    # Construct features dictionary
    # 각 값을 파이썬의 기본 float로 변환하여 JSON 직렬화 문제 해결
    features = {
        "pitch_range": float(round(pitch_range, 2)),
        "loudness_std": float(round(loudness_std, 2)),
        "pause_ratio": float(round(pause_ratio, 3)),
        "speech_rate": float(round(speech_rate, 2)),
        "jitter": float(round(jitter, 4)),
        "shimmer": float(round(shimmer, 4))
    }

    # === JSON 저장 ===
    json_path = None
    if save_json:
        json_path = os.path.splitext(wav_path)[0] + "_features.json"
        try:
            with open(json_path, "w") as f:
                json.dump(features, f, indent=4)
                f.flush()                # 버퍼를 강제로 비움
                os.fsync(f.fileno())     # OS 레벨에서 디스크에 기록 강제
            print(f"✅ Features saved to {json_path}")
        except Exception as e:
            print(f"❌ Failed to save JSON: {e}")
            json_path = None

    if save_json:
        return features, json_path
    else:
        return features
