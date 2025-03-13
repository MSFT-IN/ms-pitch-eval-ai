import tiktoken

from base_call import call_gpt

def call_gpt_for_feedback(text_chunk):
    """
    Function to call GPT for feedback on the text chunk.

    Args:
        text_chunk (str): Text chunk to provide feedback on.
    Returns:
        feedback (str): Feedback on the text chunk.
    """

    max_tokens = 1000

    system_prompt = "https://learn.microsoft.com/ko-kr/의 최신 정보를 기반으로, 틀린 내용을 지적해줘."

    user_base_prompt = f"bullet point로, 완전히 틀린 내용만 그 근거와 함께 간략히 지적해줘. 근거는 https://learn.microsoft.com/ko-kr/에서 찾아. 다른 말은 덧붙이지 마. 텍스트: "
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



# TODO: Gounding with Bing Search for efficient RAG
def grounding_w_bing():
    pass



def run_feedback_flow(chunks):
    """
    Function to run the feedback flow on the text chunks.
    
    Args:
        chunks (list): List of text chunks to provide feedback on.
    Returns:
        feedback_text (str): Feedback on the text chunks.
    """
    
    feedback_text = ""

    for chunk in chunks:
        feedback = call_gpt_for_feedback(chunk)
        feedback_text += feedback + " "
    
    return feedback_text