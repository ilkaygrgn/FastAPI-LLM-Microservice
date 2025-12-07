# app/services/llm_service.py

import json
# from openai import OpenAI, api_key
from app.core.config import settings
from typing import Generator, List, Dict
from app.db.redis_client import redis_client
from app.workers.tasks import update_user_profile_task
from app.db.database import SessionLocal
from app.models.user import User

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


def generate_chat_response_sync(messages: List[Dict[str, str]]) -> str:
    """Generates a synchronous Gemini response."""
    
    prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])

    response = client.models.generate_content(
        model=settings.GOOGLE_LLM_MODEL,
        contents=prompt,
    )

    return response.text


"""
History Management
"""     
from app.services.chat_history import get_session_history, add_message_to_history
from app.services.vector_db_service import get_vector_store


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

    #  Retrive user profile from the database for long-term memory update
    user_profile_data = "No profile established."
    with SessionLocal() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.user_profile:
            user_profile_data = user.user_profile

    # 3. Construct message list for the API call
    
    # The final list of messages to send to the API is the formatted history
    # plus the formatted current message.
    messages = formatted_history
    messages.append(format_for_gemini(raw_user_msg_dict))

    """
    # **PHASE 4: RAG Retrieval**
    """
    vector_store = get_vector_store()
    # Retrieve top 4 most relevant chunks based on the user's current message
    retrieved_docs = vector_store.similarity_search(user_message, k=4)
    
    # Format the retrieved documents into a context string
    rag_context = "\n---\n".join([doc.page_content for doc in retrieved_docs])
    """
    RAG retrieval
    """

    #system_prompt = "You are a helpful, senior Python and LLM engineering assistant. Be concise and professional."
    # Add user profile to the system prompt
    system_prompt = f"""
    You are a helpful, senior Python and LLM engineering assistant. Be concise and professional.
    
    --- RAG KNOWLEDGE BASE ---
    Use the following retrieved context to answer the user's question accurately. If the context does not contain the answer, state that you cannot find the answer in the provided documents.
    Context: {rag_context}
    ---

    --- USER PROFILE ---
    {user_profile_data}
    ---
    
    Maintain context based on the profile and the conversation history.
    """

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

            # trigger log-term memory update
            update_user_profile_task.delay(user_id, session_id)

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