import openai
import logging
from config import OPENAI_API_KEY, GPT_MODEL

def summarize_transcript(transcript_text):
    """
    Summarize a transcript using OpenAI's GPT model
    
    Args:
        transcript_text (str): The transcript text to summarize
        
    Returns:
        str: The summarized transcript
    """
    if not transcript_text:
        logging.error("Cannot summarize empty transcript")
        return None
    
    try:
        logging.info(f"Summarizing transcript of length {len(transcript_text)}")
        
        # Use OpenAI to summarize the transcript
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        # Create a detailed prompt with specific instructions
        prompt = f"""
        Analyze and summarize the following meeting transcript in a structured format. 
        
        Your summary should include:
        1. MEETING OVERVIEW: A concise 2-3 sentence overview of what the meeting was about.
        2. KEY TOPICS: List the main topics discussed, with brief explanations of each.
        3. DECISIONS MADE: Clearly identify any decisions reached during the meeting.
        4. ACTION ITEMS: Extract all action items, including who is responsible and any deadlines mentioned.
        5. FOLLOW-UP: Note any planned follow-up meetings or future discussion points.
        6. CONCLUSIONS: Summarize the overall outcomes and next steps discussed.
        
        Format your summary with clear headings for each section. Be comprehensive yet concise, focusing on the substance of the discussion rather than conversational elements.
        
        TRANSCRIPT:
        {transcript_text}
        """
        
        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert meeting analyst and professional executive assistant. Your specialty is extracting the most important information from meeting transcripts and organizing it into clear, structured summaries that capture all key points, decisions, and action items. You focus on business value and actionable insights, eliminating small talk and irrelevant discussions."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=3000,
            temperature=0.3
        )
        
        summary = response.choices[0].message.content.strip()
        
        logging.info(f"Generated summary of length {len(summary)}")
        return summary
        
    except Exception as e:
        logging.error(f"Error summarizing transcript: {str(e)}")
        return None 