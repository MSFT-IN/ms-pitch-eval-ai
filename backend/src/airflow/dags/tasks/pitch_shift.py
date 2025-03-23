import os
import numpy as np
import parselmouth
import pyworld as pw
import soundfile as sf



def pitch_shift(input_wav, target_pitch=160):
    # 오디오 로드
    y, sr = sf.read(input_wav)
    if y.ndim > 1:
        y = y.mean(axis=1)  # 스테레오를 모노로 변환

    # WORLD 분석
    _f0, t = pw.harvest(y, sr)
    sp = pw.cheaptrick(y, _f0, t, sr)
    ap = pw.d4c(y, _f0, t, sr)

    # 현재 평균 피치 계산
    mean_f0 = np.mean(_f0[_f0 > 0])
    print(mean_f0)
    print(mean_f0)
    if np.isnan(mean_f0):
        raise ValueError("유효한 피치를 찾을 수 없습니다.")

    # 피치 시프팅 비율 계산
    ratio = target_pitch / mean_f0

    # 피치 시프팅 적용
    f0_shifted = _f0 * ratio

    # WORLD 합성
    y_shifted = pw.synthesize(f0_shifted, sp, ap, sr)

    # 출력 파일명 생성
    base, ext = os.path.splitext(input_wav)
    output_wav = f"{base}_{int(mean_f0)}_pitched.wav"

    # 파일 저장
    sf.write(output_wav, y_shifted, sr)

    return output_wav