import tiktoken
from base_call import call_gpt



def call_gpt_for_feedback(pitch_purpose, text_chunk):
    """
    Function to call GPT for feedback on the text chunk.

    Args:
        text_chunk (str): Text chunk to provide feedback on.
    Returns:
        feedback (str): Feedback on the text chunk.
    """

    max_tokens = 1000

    system_prompt = "mslearn에서 검색한 최신 정보를 기반으로, 틀린 내용을 지적해줘."

    user_base_prompt = f"명칭이나 개수에 대한 사소한 지적은 하지 마. 맥락을 고려했을 때에도 기능 설명 자체가 명백히 틀린 것만 지적해줘. 근거는 mslearn 사이트에서 찾고 citation을 붙여줘. - bullet point로 지적을 정리해줘. bullet point 외의 설명은 하지 마. 텍스트: "
    user_prompt = user_base_prompt + text_chunk
    
    encoding = tiktoken.get_encoding("cl100k_base")
    if len(encoding.encode(system_prompt+user_prompt)) <= max_tokens/2:
        feedback = call_gpt(system_prompt, user_prompt, max_tokens)
        print(feedback)
        return feedback
    else:
        # TODO: Implement chunking for large text
        print("Token limit exceeded.")
        return "Token limit exceeded."



def generate_content_feedback(pitch_purpose, chunks):
    """
    Function to run the feedback flow on the text chunks.
    
    Args:
        chunks (list): List of text chunks to provide feedback on.
    Returns:
        feedback_chunks (list): List of feedback on the text chunks.
    """
    
    feedback_chunks = []

    # Exclude the first and last chunks
    feedback_chunks.append("N/A")
    for chunk in chunks[1:-1]:
        feedback = call_gpt_for_feedback(pitch_purpose, chunk)
        feedback_chunks.append(feedback)
    feedback_chunks.append("N/A")
    
    return feedback_chunks