# app/services/llm_service.py

import json
from openai import OpenAI, api_key
from app.core.config import settings
from typing import Generator, List, Dict
from app.db.redis_client import redis_client

from google import genai


# Initialize OpenAI client using the API key from the config
#client = OpenAI(api_key=settings.OPENAI_API_KEY)
client = genai.Client(api_key=settings.GOOGLE_API_KEY)

def stream_chat_response(messages: List[Dict[str, str]]) -> Generator[str, None, None]:
    """Streams a Gemini response chunk-by-chunk."""
    try:
        # Convert OpenAI-style messages → Gemini text format
        prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])

        stream = client.models.generate_content_stream(
            model=settings.GOOGLE_LLM_MODEL,
            contents=prompt,
        )

        for chunk in stream:
            if chunk.text:
                yield chunk.text

    except Exception as e:
        yield f"ERROR: Gemini API call failed: {str(e)}"
# def stream_chat_response(messages: List[Dict[str, str]]) -> Generator[str, None, None]:
#     """Connects to the OpenAI API and streams the response content chunk by chunk"""
#     try:
#         stream = client.chat.completions.create(
#             #model=settings.LLM_MODEL,
#             model=settings.GOOGLE_LLM_MODEL,
#             messages=messages,
#             stream=True
#         )
#         for chunk in stream:
#             # Check if content exists and yield it
#             content = chunk.choices[0].delta.content
#             if content is not None:
#                 yield content
#     except Exception as e:
#         yield f"ERROR: LLM API call failed: {str(e)}"

# A non-streaming version for background tasks (optional, but good practice)

def generate_chat_response_sync(messages: List[Dict[str, str]]) -> str:
    """Generates a synchronous Gemini response."""
    
    prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])

    response = client.models.generate_content(
        model=settings.GOOGLE_LLM_MODEL,
        contents=prompt,
    )

    return response.text

# def generate_chat_response_sync(messages: List[Dict[str, str]]) -> str:
#     """Generates a chat response synchronously (for background tasks)"""
#     response = client.chat.completions.create(
#         #model=settings.LLM_MODEL,
#         model=settings.GOOGLE_LLM_MODEL,
#         messages=messages,
#         stream=False
#     )
#     return response.choices[0].message.content


"""
History Management
"""     
# Key template for storing history:
HISTORY_KEY = "chat_history:{user_id}:{session_id}"
MAX_HISTORY_LENGTH = 10 # Keep the last 10 messages (5 user, 5 assistant)

def get_session_history(user_id: str, session_id: str) -> List[Dict[str, str]]:
    """Retrieves the chat history for a given user and session from Redis"""
    if not redis_client:
        return []

    key = HISTORY_KEY.format(user_id=user_id, session_id=session_id)
    # LTRIM keeps the history size bounded (short-term memory window)
    history_json = redis_client.lrange(key, -MAX_HISTORY_LENGTH, -1)

    return [json.loads(msg) for msg in history_json]

def add_message_to_history(user_id: str, session_id: str, message: Dict[str, str]):
    """Adds a message to the chat history for a given user and session in Redis"""
    if not redis_client:
        return
    key = HISTORY_KEY.format(user_id=user_id, session_id=session_id)
    # LPUSH adds to the left (head). LTRIM can then easily keep the length bounded.
    redis_client.rpush(key, json.dumps(message))
    # Keep the list size bounded
    redis_client.ltrim(key, -MAX_HISTORY_LENGTH, -1)


# app/services/llm_service.py (Fixed for Gemini API content structure)

from google import genai
from app.core.config import settings
from typing import Generator, List, Dict
# Assuming 'client' is initialized and helper functions are available

def format_for_gemini(message: Dict[str, str]) -> Dict:
    """Transforms a simple {'role': 'user', 'content': 'text'} dict 
    into the Gemini API required format."""
    
    # Ensure role is correctly mapped for history (model for assistant)
    role = message['role']
    if role == 'assistant':
        role = 'model'
        
    return {
        "role": role,
        "parts": [
            {"text": message['content']}
        ]
    }


def stream_chat_response_with_history(
    user_id: str, 
    session_id: str, 
    user_message: str
) -> Generator[str, None, None]:
    
    # 1. Retrieve and FORMAT history
    # The history retrieved from Redis is in the simple {'role': 'user', 'content': 'text'} format
    raw_history = get_session_history(user_id, session_id)
    
    # Convert all history items to the required Gemini API format
    formatted_history = [format_for_gemini(msg) for msg in raw_history]
    
    
    # 2. Prepare the current user message and save it (using the simple format for Redis)
    raw_user_msg_dict = {"role": "user", "content": user_message}
    add_message_to_history(user_id, session_id, raw_user_msg_dict)

    # 3. Construct message list for the API call
    
    # The final list of messages to send to the API is the formatted history
    # plus the formatted current message.
    messages = formatted_history
    messages.append(format_for_gemini(raw_user_msg_dict))

    system_prompt = "You are a helpful, senior Python and LLM engineering assistant. Be concise and professional."


    # 4. Stream response and capture full message (Gemini API Call)
    full_response_content = ""
    try:
        stream = client.models.generate_content_stream(
            #model=settings.LLM_MODEL,
            model=settings.GOOGLE_LLM_MODEL,
            contents=messages, # Now contains the correctly structured list of dictionaries
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt
            )
        )
        for chunk in stream:
            content = chunk.text
            if content:
                full_response_content += content
                yield content

    except Exception as e:
        yield f"ERROR: Gemini API call failed: {str(e)}"
        
    finally:
        # 5. Add full assistant response to history (using simple format for Redis)
        if full_response_content:
            # IMPORTANT: Save the history using the simple 'assistant' role for easy retrieval later
            assistant_msg_dict = {"role": "assistant", "content": full_response_content}
            add_message_to_history(user_id, session_id, assistant_msg_dict)

# # Update the primary streaming function:
# def stream_chat_response_with_history(user_id: str, session_id: str, user_message: str) -> Generator[str, None, None]:
    
#     # 1. Retrieve history
#     history = get_session_history(user_id, session_id)
    
#     # 2. Add current user message to memory (immediately, in case of failure later)
#     user_msg_dict = {"role": "user", "content": user_message}
#     add_message_to_history(user_id, session_id, user_msg_dict)

#     # 3. Construct message list for the LLM
#     messages = [
#         {"role": "system", "content": "You are a helpful, senior Python and LLM engineering assistant. Be concise and professional."},
#     ]
#     messages.extend(history) # Append previous messages
#     messages.append(user_msg_dict) # Append current user message

#     # 4. Stream response and capture full message
#     full_response_content = ""
#     try:
#         stream = client.chat.completions.create(
#             model=settings.LLM_MODEL,
#             messages=messages,
#             stream=True,
#         )
#         for chunk in stream:
#             content = chunk.choices[0].delta.content
#             if content:
#                 full_response_content += content
#                 yield content

#     finally:
#         # 5. Add full assistant response to history
#         if full_response_content:
#             assistant_msg_dict = {"role": "assistant", "content": full_response_content}
#             add_message_to_history(user_id, session_id, assistant_msg_dict)