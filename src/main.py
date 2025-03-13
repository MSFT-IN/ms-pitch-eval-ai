from run_stt import run_stt_flow
from content_feedback import run_feedback_flow

if __name__ == "__main__":
    pitch_purpose = "보안을 위한 코파일럿 사용"
    refined_text, refined_chunks = run_stt_flow(pitch_purpose)
    feedback = run_feedback_flow(refined_chunks)
    print("\n\n\nContent Feedback Based on MSLearn:", feedback)
