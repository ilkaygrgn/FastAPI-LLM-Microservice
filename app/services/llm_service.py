# app/services/llm_service.py

import json
from app.core.config import settings
from typing import Generator, List, Dict
from app.db.redis_client import redis_client
from app.workers.tasks import update_user_profile_task
from app.db.database import SessionLocal
from app.models.user import User

from google import genai

client = genai.Client(api_key=settings.GOOGLE_API_KEY)

def stream_chat_response(messages: List[Dict[str, str]]) -> Generator[str, None, None]:
    """Streams a Gemini response chunk-by-chunk."""
    try:
        
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
        if retrieved_docs:
            pass # We wait for model confirmation
        rag_context = "\n---\n".join([doc.page_content for doc in retrieved_docs])

    # 6. System Prompt
    system_prompt = f"""
    You are a senior AI Assistant with access to real-time tools.
    
    --- MANDATORY INSTRUCTION ---
    If a user asks for stock prices or to schedule a meeting, you MUST use the provided tools. 
    
    --- RAG INSTRUCTION ---
    If you use the provided "RAG KNOWLEDGE BASE" context to derive your answer, you MUST start your response with the tag [RAG]. 
    If you do not use the context (e.g. for general chatter), do NOT use the tag.
    
    --- RAG KNOWLEDGE BASE ---
    {f"Context: {rag_context}" if use_rag else "No external documents provided."}
    
    --- USER PROFILE ---
    {user_profile_data}
    """

    final_response_stream = None
    full_response_content = ""

    # 7. Unified API Call (Handles both Chat and Tools)
    # We use a loop to handle optional Function Calling "turns"
    current_messages = messages
    
    while True:
        try:
            print(f"DEBUG: Initiating Stream. Tools enabled: {enable_tools}")
            
            # Disable automatic function calling so we can intercept and separate the "Thought"
            stream = client.models.generate_content_stream(
                model=settings.GOOGLE_LLM_MODEL,
                contents=current_messages,
                config=genai.types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    tools=list(TOOL_MAP.values()) if enable_tools else None,
                    automatic_function_calling=genai.types.AutomaticFunctionCallingConfig(disable=True) 
                )
            )
            
            function_calls_in_progress = []
            text_response_started = False

            for chunk in stream:
                # A chunk might contain text OR a function call (or both, though rare in one chunk)
                
                # Check for Function Calls
                # Access via candidates -> content -> parts -> function_call is standard for the proto structure
                if chunk.candidates:
                    for i, candidate in enumerate(chunk.candidates):
                        if hasattr(candidate, 'content') and candidate.content and hasattr(candidate.content, 'parts'):
                            for part in candidate.content.parts:
                                if part.function_call:
                                    fc = part.function_call
                                    function_calls_in_progress.append(fc)
                                    # Yield a "Thought" event to the frontend
                                    print(f"DEBUG: Yielding Thought for {fc.name}", flush=True)
                                    yield json.dumps({
                                        "type": "thought", 
                                        "content": f"🔍 Agent is executing tool: {fc.name}..."
                                    }) + "\n"
                        # Fallback/Alternative check using SDK helper properties if available
                        elif hasattr(candidate, 'function_calls') and candidate.function_calls:
                             for fc in candidate.function_calls:
                                function_calls_in_progress.append(fc)
                                print(f"DEBUG: Yielding Thought (via helper) for {fc.name}", flush=True)
                                yield json.dumps({
                                    "type": "thought", 
                                    "content": f"🔍 Agent is executing tool: {fc.name}..."
                                }) + "\n"
                
                # Check for Text
                # Note: chunk.text raises ValueError if no text part is present, so check parts first
                # chunk.text is a helper property on the response that aggregates text from the first candidate
                try:
                    if chunk.text:
                        text_content = chunk.text
                        text_response_started = True
                        
                        # Check for RAG usage tag
                        if "[RAG]" in text_content:
                             # Emit RAG thought
                             yield json.dumps({
                                "type": "thought",
                                "content": "📚 RAG: Retrieved context from knowledge base."
                             }) + "\n"
                             # Strip the tag from the output
                             text_content = text_content.replace("[RAG]", "").lstrip()

                        if text_content:
                            full_response_content += text_content
                            yield json.dumps({
                                "type": "text", 
                                "content": text_content
                            }) + "\n"
                except Exception:
                    # chunk.text might raise if no text is present (e.g. only function call)
                    pass

            # End of stream for this turn.
            
            # If we collected function calls, we must execute them and loop back.
            if function_calls_in_progress:
                
                # 1. Add model's request to history (REQUIRED by Gemini)
                # We need to construct a Content object resembling what the model just produced
                # This is tricky with streaming chunks, but usually the last chunk or aggregated parts suffice.
                # Because we are in a manual loop, we need to append the Tool Use request to the messages.
                
                # Reconstruct the "model" turn that requested the tool
                # Create a Part for each function call
                parts = []
                for fc in function_calls_in_progress:
                    parts.append(genai.types.Part.from_function_call(name=fc.name, args=dict(fc.args)))
                
                if text_response_started:
                     # If the model also said something, include it (rare for pure tool use but possible)
                     # For simplicity, we assume text came first or parallel. 
                     # Standard Gemini flow is usually Tool Call OR Text.
                     pass 

                current_messages.append(genai.types.Content(role="model", parts=parts))

                # 2. Execute Tools
                function_results = []
                for fc in function_calls_in_progress:
                    func_name = fc.name
                    func_args = dict(fc.args)

                    if func_name in TOOL_MAP:
                        print(f"DEBUG: Executing tool {func_name}")
                        try:
                            # Execute the actual Python function
                            tool_result = TOOL_MAP[func_name](**func_args)
                            
                            # Update Frontend that we are done
                            print(f"DEBUG: Yielding Completion Thought for {func_name}", flush=True)
                            yield json.dumps({
                                "type": "thought", 
                                "content": f"✅ Tool {func_name} completed."
                            }) + "\n"

                        except Exception as e:
                            tool_result = f"Error executing tool: {str(e)}"
                            yield json.dumps({
                                "type": "thought", 
                                "content": f"❌ Tool {func_name} failed."
                            }) + "\n"

                        # Create the Function Response Part
                        function_results.append(
                            genai.types.Part.from_function_response(
                                name=func_name,
                                response={"result": str(tool_result)}
                            )
                        )
                
                # 3. Add Tool Results to history
                current_messages.append(genai.types.Content(role="tool", parts=function_results))
                
                # 4. LOOP BACK to let the model generate the final answer based on the tool result
                continue

            else:
                # No function calls? Then we are done.
                break

        except Exception as e:
            print(f"CRITICAL ERROR: {str(e)}")
            yield json.dumps({
                "type": "text", 
                "content": f"\n[Error: {str(e)}]"
            }) + "\n"
            return
    
    # Finally block equivalent to save history handled below loop
    # 9. Save Assistant Response & Trigger Memory Update
    if full_response_content:
        assistant_msg_dict = {"role": "assistant", "content": full_response_content}
        # Note: We are saving only the final TEXT response to Redis for simplicity in this demo.
        # Ideally we save the whole chain, but for the 'chat history' displayed to user, text is key.
        add_message_to_history(user_id, session_id, assistant_msg_dict)
        update_user_profile_task.delay(user_id, session_id)
