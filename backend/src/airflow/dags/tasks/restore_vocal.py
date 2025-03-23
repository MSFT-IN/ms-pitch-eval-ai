from voicefixer import VoiceFixer
import os




def voicefixer_enhance(input_wav, output_wav=None):
    """
    VoiceFixer로 음성 복원 및 업샘플링 (보통 16kHz → 44.1kHz)
    
    - 입력 파일명을 기반으로 "_enhanced"를 추가한 파일명으로 저장합니다.
    - output_wav 인자가 None이면, 입력 파일명에 _enhanced 를 붙여 현재 디렉토리에 저장합니다.
    
    Args:
        input_wav (str): 입력 WAV 파일 경로.
        output_wav (str, optional): 저장할 출력 파일 경로. 기본값은 None.
        
    Returns:
        str: 복원된 음성이 저장된 파일 경로.
    """
    if output_wav is None:
        base, ext = os.path.splitext(os.path.basename(input_wav))
        output_wav = f"{base}_enhanced.wav"
    print("VoiceFixer 모델로드중")    

    vf = VoiceFixer()

    print("VoiceFixer로 업샘플링 + 복원 중...")
    vf.restore(input=input_wav, output=output_wav)
    print(f" 완료: {output_wav}")
    return output_wav