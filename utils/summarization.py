import openai
import logging
from config import OPENAI_API_KEY

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
        
        # Create the prompt with instructions
        prompt = f"""
        Summarize the following meeting transcript. Focus on key points, decisions, and action items.
        Include the main topics discussed and any conclusions reached.
        
        TRANSCRIPT:
        {transcript_text}
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes meeting transcripts."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.3
        )
        
        summary = response.choices[0].message.content.strip()
        
        logging.info(f"Generated summary of length {len(summary)}")
        return summary
        
    except Exception as e:
        logging.error(f"Error summarizing transcript: {str(e)}")
        return None 