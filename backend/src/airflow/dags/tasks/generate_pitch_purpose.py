from tasks.base_call import call_gpt

def get_pitch_purpose(recognized_chunks):
    """
    Function to retrieve the pitch purpose by analyzing the first two chunks of recognized text.
    
    Args:
        recognized_chunks (list): List of recognized text chunks.
    Returns:
        pitch_purpose (str): Retrieved pitch purpose.
    """
    
    if len(recognized_chunks) < 2:
        return "Microsoft 세일즈 피치"
        # raise ValueError("Not enough recognized chunks to determine pitch purpose.")
    
    # Combine the first two chunks for analysis
    combined_chunks = " ".join(recognized_chunks[:2])
    
    # Define system and user prompts for GPT
    system_prompt = "세일즈 피치의 목적을 판단해줘."
    user_prompt = f"다음 내용이 마이크로소프트의 어떤 서비스에 대한 피치인지 판단해줘. 부연 설명 없이 피치 목적만을 리턴해줘.: {combined_chunks}"
    
    # Call GPT to retrieve the pitch purpose
    pitch_purpose = call_gpt(system_prompt, user_prompt)
    
    return pitch_purpose
