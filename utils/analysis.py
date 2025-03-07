import logging
import json
from config import OPENAI_API_KEY, GPT_MODEL
from models.meeting import ActionItem

def analyze_transcript(transcript, meeting_title=None):
    """
    Analyze the meeting transcript using OpenAI GPT to extract summary and action items
    
    Args:
        transcript (str): The meeting transcript text
        meeting_title (str, optional): The title of the meeting
        
    Returns:
        tuple: (summary, action_items)
    """
    try:
        logging.info("Starting transcript analysis")
        
        # Create a prompt for the GPT model
        context = f"Meeting Title: {meeting_title}\n\n" if meeting_title else ""
        
        prompt = f"""
        {context}
        Here is a transcript from a meeting:
        
        {transcript}
        
        Please analyze this meeting transcript and provide:
        1. A concise summary of the key points discussed (500 words max)
        2. A list of action items with the following details for each:
           - Description of the task
           - Person assigned to (if mentioned)
           - Due date (if mentioned)
        
        Format your response as JSON with the following structure:
        {{
            "summary": "summary text here",
            "action_items": [
                {{
                    "description": "task description",
                    "assigned_to": "person name or null if not specified",
                    "due_date": "YYYY-MM-DD or null if not specified"
                }}
            ]
        }}
        
        Ensure the action items are concrete, actionable tasks rather than general discussion points.
        """
        
        # Import here to handle different versions of the OpenAI SDK
        import openai
        
        # Try newer API first, fall back to older if needed
        try:
            # Newer OpenAI API
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model=GPT_MODEL,
                messages=[
                    {"role": "system", "content": "You are an AI assistant that specializes in analyzing meeting transcripts and extracting key information."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more focused results
                response_format={"type": "json_object"}
            )
            result_content = response.choices[0].message.content
        except (AttributeError, ImportError, TypeError):
            # Older OpenAI API
            if hasattr(openai, 'api_key'):
                openai.api_key = OPENAI_API_KEY
                
            response = openai.ChatCompletion.create(
                model=GPT_MODEL,
                messages=[
                    {"role": "system", "content": "You are an AI assistant that specializes in analyzing meeting transcripts and extracting key information."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more focused results
                response_format={"type": "json_object"}
            )
            result_content = response.choices[0].message.content
        
        # Extract and parse the JSON response
        result = json.loads(result_content)
        
        summary = result.get("summary", "")
        action_items_raw = result.get("action_items", [])
        
        # Convert raw action items to ActionItem objects
        action_items = []
        for item in action_items_raw:
            due_date = None
            if item.get("due_date"):
                try:
                    from datetime import datetime
                    due_date = datetime.strptime(item["due_date"], "%Y-%m-%d")
                except:
                    pass
                    
            action_items.append(ActionItem(
                description=item["description"],
                assigned_to=item.get("assigned_to"),
                due_date=due_date,
                status="pending"
            ))
        
        logging.info(f"Analysis completed. Summary length: {len(summary)}. Action items: {len(action_items)}")
        
        return summary, action_items
        
    except Exception as e:
        logging.error(f"Error analyzing transcript: {e}")
        raise


def extract_participants(transcript):
    """
    Attempt to identify meeting participants from the transcript
    
    Args:
        transcript (str): The meeting transcript
        
    Returns:
        list: List of participant names
    """
    try:
        prompt = f"""
        Here is a transcript from a meeting:
        
        {transcript}
        
        Please identify the names of all participants mentioned in this meeting. 
        Return a JSON object with a 'participants' field containing an array of unique names.
        Example: {{"participants": ["John Smith", "Jane Doe", "Alice Johnson"]}}
        """
        
        # Import here to handle different versions of the OpenAI SDK
        import openai
        
        # Try newer API first, fall back to older if needed
        try:
            # Newer OpenAI API
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model=GPT_MODEL,
                messages=[
                    {"role": "system", "content": "You are an AI assistant that extracts participant names from meeting transcripts."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            result_content = response.choices[0].message.content
        except (AttributeError, ImportError, TypeError):
            # Older OpenAI API
            if hasattr(openai, 'api_key'):
                openai.api_key = OPENAI_API_KEY
                
            response = openai.ChatCompletion.create(
                model=GPT_MODEL,
                messages=[
                    {"role": "system", "content": "You are an AI assistant that extracts participant names from meeting transcripts."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            result_content = response.choices[0].message.content
        
        # Extract the participants from the response
        result = json.loads(result_content)
        participants = result.get("participants", [])
        
        logging.info(f"Extracted {len(participants)} participants from transcript")
        
        return participants
        
    except Exception as e:
        logging.error(f"Error extracting participants: {e}")
        return []