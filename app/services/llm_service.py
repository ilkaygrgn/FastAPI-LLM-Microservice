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
from app.tools.agent_tools import get_real_time_stock_price, schedule_meeting

#Map function names to the actual callable functions
TOOL_MAP = {
    "get_real_time_stock_price": get_real_time_stock_price,
    "schedule_meeting": schedule_meeting,
}

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
    user_message: str,
    enable_tools: bool = False,
    use_rag: bool = False, 
) -> Generator[str, None, None]:
    
    # 1. Retrieve and Format History
    raw_history = get_session_history(user_id, session_id)
    formatted_history = [format_for_gemini(msg) for msg in raw_history]
    
    # 2. Save User Message
    raw_user_msg_dict = {"role": "user", "content": user_message}
    add_message_to_history(user_id, session_id, raw_user_msg_dict)

    # 3. Retrieve User Profile
    user_profile_data = "No profile established."
    with SessionLocal() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.user_profile:
            user_profile_data = user.user_profile

    # 4. Construct Messages List
    messages = formatted_history + [format_for_gemini(raw_user_msg_dict)]

    # 5. RAG Retrieval
    rag_context = ""
    if use_rag:
        vector_store = get_vector_store()
        retrieved_docs = vector_store.similarity_search(user_message, k=4)
        rag_context = "\n---\n".join([doc.page_content for doc in retrieved_docs])

    # 6. System Prompt
    system_prompt = f"""
    You are a senior AI Assistant with access to real-time tools.
    
    --- MANDATORY INSTRUCTION ---
    If a user asks for stock prices or to schedule a meeting, you MUST use the provided tools. 
    
    --- RAG KNOWLEDGE BASE ---
    {f"Context: {rag_context}" if use_rag else "No external documents provided."}
    
    --- USER PROFILE ---
    {user_profile_data}
    """

    final_response_stream = None
    full_response_content = ""

    # 7. Unified API Call (Handles both Chat and Tools)
    try:
        print(f"DEBUG: Initiating Unified Stream. Tools enabled: {enable_tools}")
        
        # We pass tools and set automatic calling. 
        # If no tool is needed, it just chats. If a tool IS needed, it calls it and then chats.
        final_response_stream = client.models.generate_content_stream(
            model=settings.GOOGLE_LLM_MODEL,
            contents=messages,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                tools=list(TOOL_MAP.values()) if enable_tools else None,
                # This is the magic: it handles the 'Model -> Tool -> Model' loop for you
                automatic_function_calling=genai.types.AutomaticFunctionCallingConfig(disable=False) if enable_tools else None
            )
        )
    except Exception as e:
        print(f"CRITICAL ERROR: {str(e)}")
        yield f"ERROR: LLM stream failed: {str(e)}"
        return

    # 8. Yield chunks to Swagger/Frontend
    try:
        for chunk in final_response_stream:
            # The SDK might yield chunks for the tool call itself; 
            # we only care about the final text for the user.
            if chunk.text:
                full_response_content += chunk.text
                yield chunk.text

    except Exception as e:
        yield f"ERROR: Streaming interrupted: {str(e)}"
        
    finally:
        # 9. Save Assistant Response & Trigger Memory Update
        if full_response_content:
            assistant_msg_dict = {"role": "assistant", "content": full_response_content}
            add_message_to_history(user_id, session_id, assistant_msg_dict)
            update_user_profile_task.delay(user_id, session_id)


# def stream_chat_response_with_history(
#     user_id: str, 
#     session_id: str, 
#     user_message: str,
#     enable_tools: bool = False,# <-- Control switch for Function Calling
#     use_rag: bool = False, # <-- Control switch for RAG
# ) -> Generator[str, None, None]:
    
#     # 1. Retrieve and FORMAT history
#     # The history retrieved from Redis is in the simple {'role': 'user', 'content': 'text'} format
#     raw_history = get_session_history(user_id, session_id)
    
#     # Convert all history items to the required Gemini API format
#     formatted_history = [format_for_gemini(msg) for msg in raw_history]
    
    
#     # 2. Prepare the current user message and save it (using the simple format for Redis)
#     raw_user_msg_dict = {"role": "user", "content": user_message}
#     add_message_to_history(user_id, session_id, raw_user_msg_dict)

#     #  Retrive user profile from the database for long-term memory update
#     user_profile_data = "No profile established."
#     with SessionLocal() as db:
#         user = db.query(User).filter(User.id == user_id).first()
#         if user and user.user_profile:
#             user_profile_data = user.user_profile

#     # 3. Construct message list for the API call
    
#     # The final list of messages to send to the API is the formatted history
#     # plus the formatted current message.
#     messages = formatted_history
#     messages.append(format_for_gemini(raw_user_msg_dict))

#     """
#     # **PHASE 4: RAG Retrieval**
#     """
#     rag_context = ""
#     if use_rag:
#         vector_store = get_vector_store()
#         # Retrieve top 4 most relevant chunks based on the user's current message
#         retrieved_docs = vector_store.similarity_search(user_message, k=4)
        
#         # Format the retrieved documents into a context string
#         rag_context = "\n---\n".join([doc.page_content for doc in retrieved_docs])
#     """
#     RAG retrieval
#     """

#     #system_prompt = "You are a helpful, senior Python and LLM engineering assistant. Be concise and professional."
#     # Add user profile to the system prompt
#     system_prompt = f"""
#     You are a senior AI Assistant with access to real-time tools.
        
#     --- MANDATORY INSTRUCTION ---
#     If a user asks for stock prices or to schedule a meeting, you MUST use the provided tools. 
#     Do not tell the user you don't have access to data; use the functions provided to fetch it.
#     ------------------------------
#     --- RAG KNOWLEDGE BASE ---
#     {f"Use the following retrieved context to answer the user's question accurately. If the context does not contain the answer, state that you cannot find the answer in the provided documents.Context: {rag_context}" if use_rag else ""}
#     ---

#     --- USER PROFILE ---
#     {user_profile_data}
#     ---
    
#     Maintain context based on the profile and the conversation history.
#     """

#     # 4. Stream response and capture full message (Gemini API Call)
#     final_response_stream = None
#     full_response_content = ""

#     if enable_tools:
#         # 4. INITIAL API Call (Non-Streaming to Check for Tool Use)
#         print(f"DEBUG: Entering Tool Logic block (v123)")
#         print(f"DEBUG: Sending {len(messages)} items in history to Gemini.")
#         try:
#             print("DEBUG: Calling client.models.generate_content...")
#             response = client.models.generate_content(
#                 model=settings.GOOGLE_LLM_MODEL,
#                 contents=messages,
#                 config=genai.types.GenerateContentConfig(
#                     system_instruction=system_prompt,
#                     tools=list(TOOL_MAP.values()),
#                     # This tells the SDK to automatically handle the tool execution
#                     automatic_function_calling=genai.types.AutomaticFunctionCallingConfig(disable=False)
#                 )
#             )
#             print("DEBUG: Unified stream initiated successfully.")
#         except Exception as e:
#             # This will show you exactly why the API call failed (e.g., "Invalid API Key", "400 Bad Request")
#             print(f"CRITICAL ERROR in Gemini API Call: {str(e)}")
#             yield f"ERROR: Gemini API call failed: {str(e)}"
#             return

#         # 5. Tool Use Logic Loop
#         if response.function_calls:
#             # Execute tool(s) and append results to messages list...
#             function_results = []

#             # --- CRITICAL UPDATE #1: Add the Model's "Decision" to messages ---
#             # Gemini MUST see that it asked for the tool before you give it the answer.
#             messages.append(response.candidates[0].content)
#             print(f"DEBUG:Tool executed v12")
#             for call in response.function_calls:
#                 func_name = call.name
#                 func_args = dict(call.args)

#                 if func_name in TOOL_MAP:
#                     function_to_call = TOOL_MAP[func_name]
#                     tool_result = function_to_call(**func_args)
#                     print(f"DEBUG:Tool executed v1")
#                     # --- CRITICAL UPDATE #2: Standardize the result format ---
#                     function_results.append(
#                         genai.types.Part.from_function_response(
#                             name=func_name,
#                             response={"result": str(tool_result)} # Ensure result is a string/serializable
#                         )
#                     )
#                     print(f"DEBUG:Tool executed: {func_name}. Result: {tool_result}")

#                     # function_results.append(
#                     #     genai.types.Part.from_function_response(
#                     #         name=func_name,
#                     #         response={"result": tool_result}
#                     #     )
#                     # )
#                     # print(f"Tool executed: {func_name}. Result: {tool_result}")

#             #messages.append(response.candidates[0].content)
#             messages.append(genai.types.Content(role="tool", parts=function_results))

#             # Call the model a second time (streaming) to get the final response
#             final_response_stream = client.models.generate_content_stream(
#                 model=settings.GOOGLE_LLM_MODEL,
#                 contents=messages,
#                 config=genai.types.GenerateContentConfig(
#                     system_instruction=system_prompt
#                 )
#             )

#         else:
#             # If no function call, fall through to the pure streaming path (next block)
#             pass

#     # --- B. PURE STREAMING PATH (Tool Disabled or Tool Not Called) ---
#     if final_response_stream is None:
#         # This block executes if:
#         # 1. enable_tools was False OR
#         # 2. enable_tools was True, but the model did NOT request a function call.
        
#         # This is the single, direct, full-streaming call you wanted to preserve.
#         final_response_stream = client.models.generate_content_stream(
#             model=settings.GOOGLE_LLM_MODEL,
#             contents=messages,
#             config=genai.types.GenerateContentConfig(
#                 system_instruction=system_prompt,
#                 # Note: We can optionally pass tools=list(TOOL_MAP.values()) here if you
#                 # still want the model to see the tool definitions for context,
#                 # but without the intention of using them in this path. Let's omit it for simplicity.
#             )
#         )

#     # 6. Stream the Final Response and Cleanup 
#     try:
#         # Use the determined stream (from A or B)
#         for chunk in final_response_stream:
#             content = chunk.text
#             if content:
#                 full_response_content += content
#                 yield content

#     except Exception as e:
#         yield f"ERROR: Gemini API streaming failed: {str(e)}"
        
#     finally:
#         # 7. Add full assistant response to history(redis) and trigger long-term memory 
#         if full_response_content:
#             # Save the history using the simple 'assistant' role for easy retrieval later
#             assistant_msg_dict = {"role": "assistant", "content": full_response_content}
#             add_message_to_history(user_id, session_id, assistant_msg_dict)

#             # trigger log-term memory update
#             update_user_profile_task.delay(user_id, session_id)      
    

###################


# def stream_chat_response_with_history(
#     user_id: str, 
#     session_id: str, 
#     user_message: str,
#     enable_tools: bool = False,# <-- Control switch for Function Calling
# ) -> Generator[str, None, None]:
    
#     # 1. Retrieve and FORMAT history
#     # The history retrieved from Redis is in the simple {'role': 'user', 'content': 'text'} format
#     raw_history = get_session_history(user_id, session_id)
    
#     # Convert all history items to the required Gemini API format
#     formatted_history = [format_for_gemini(msg) for msg in raw_history]
    
    
#     # 2. Prepare the current user message and save it (using the simple format for Redis)
#     raw_user_msg_dict = {"role": "user", "content": user_message}
#     add_message_to_history(user_id, session_id, raw_user_msg_dict)

#     #  Retrive user profile from the database for long-term memory update
#     user_profile_data = "No profile established."
#     with SessionLocal() as db:
#         user = db.query(User).filter(User.id == user_id).first()
#         if user and user.user_profile:
#             user_profile_data = user.user_profile

#     # 3. Construct message list for the API call
    
#     # The final list of messages to send to the API is the formatted history
#     # plus the formatted current message.
#     messages = formatted_history
#     messages.append(format_for_gemini(raw_user_msg_dict))

#     """
#     # **PHASE 4: RAG Retrieval**
#     """
#     vector_store = get_vector_store()
#     # Retrieve top 4 most relevant chunks based on the user's current message
#     retrieved_docs = vector_store.similarity_search(user_message, k=4)
    
#     # Format the retrieved documents into a context string
#     rag_context = "\n---\n".join([doc.page_content for doc in retrieved_docs])
#     """
#     RAG retrieval
#     """

#     #system_prompt = "You are a helpful, senior Python and LLM engineering assistant. Be concise and professional."
#     # Add user profile to the system prompt
#     system_prompt = f"""
#     You are a helpful, senior Python and LLM engineering assistant. Be concise and professional.
    
#     --- RAG KNOWLEDGE BASE ---
#     Use the following retrieved context to answer the user's question accurately. If the context does not contain the answer, state that you cannot find the answer in the provided documents.
#     Context: {rag_context}
#     ---

#     --- USER PROFILE ---
#     {user_profile_data}
#     ---
    
#     Maintain context based on the profile and the conversation history.
#     """

#     # 4. Stream response and capture full message (Gemini API Call)
#     final_response_stream = None
#     full_response_content = ""
    
#     try:
#         stream = client.models.generate_content_stream(
#             model=settings.GOOGLE_LLM_MODEL,
#             contents=messages,
#             config=genai.types.GenerateContentConfig(
#                 system_instruction=system_prompt,
#                 tools=list(TOOL_MAP.values()), # <-- Provide the functions as tools
#             )
#         )
#         for chunk in stream:
#             content = chunk.text
#             if content:
#                 full_response_content += content
#                 yield content

#     except Exception as e:
#         yield f"ERROR: Gemini API call failed: {str(e)}"
        
#     finally:
#         # 5. Add full assistant response to history (using simple format for Redis)
#         if full_response_content:
#             # IMPORTANT: Save the history using the simple 'assistant' role for easy retrieval later
#             assistant_msg_dict = {"role": "assistant", "content": full_response_content}
#             add_message_to_history(user_id, session_id, assistant_msg_dict)

#             # trigger log-term memory update
#             update_user_profile_task.delay(user_id, session_id)

