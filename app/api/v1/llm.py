# This endpoint will handle the request and use a StreamingResponse.
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.services.llm_service import stream_chat_response, stream_chat_response_with_history
from app.schemas.chat import ChatRequest
from app.core.security import get_current_user

from app.models.user import User
from fastapi import Depends, HTTPException, status

from fastapi import Depends

router = APIRouter()

@router.post("/chat", summary="Stream a multi-turn response from the LLM")
async def chat(request: ChatRequest, current_user: User = Depends(get_current_user)):

    # Ensure a session_id is provided for multi-turn chat
    if not request.session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="session_id is required for multi-turn chat."
        )

    # Get the generator from the service layer, passing user ID and session ID
    generator = stream_chat_response_with_history(
        user_id=current_user.id, # Assumes your User model has an 'id'
        session_id=request.session_id,
        user_message=request.message
    )
    
    return StreamingResponse(generator, media_type="text/event-stream")


    # """Streams a chat response from the LLM"""

    # # In Phase 2, we will use a temporary, single-turn message list.
    # # In Phase 3, we will integrate session_id with Redis/DB for history.

    # messages = [
    #     # System Message to set the AI's personality
    #     {"role": "system", "content": "You are a helpful, senior Python and LLM engineering assistant. Be concise and professional."},
    #     # User's current message
    #     {"role": "user", "content": request.messages}
    # ]

    # # Get the generator from the service layer
    # generator = stream_chat_response(messages)
    
    # # Return the generator wrapped in FastAPI's StreamingResponse
    # # media_type 'text/event-stream' is often used for Server-Sent Events (SSE)
    # # which is ideal for streaming chat.
    # return StreamingResponse(generator, media_type="text/event-stream")