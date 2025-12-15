# This endpoint will handle the request and use a StreamingResponse.
from fastapi import APIRouter, File, UploadFile, Depends
from fastapi.responses import StreamingResponse
from app.services.llm_service import stream_chat_response, stream_chat_response_with_history
from app.schemas.chat import ChatRequest
from app.core.security import get_current_user

from app.models.user import User
from fastapi import Depends, HTTPException, status

from app.workers.tasks import index_document_task
import shutil
import os

router = APIRouter()

@router.post("/chat", summary="Stream a multi-turn response from the LLM (with optional Function Calling)")
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    enable_tools: bool = Query(
        True, 
        description="Enable Function Calling (True) for tool use, or use pure streaming (False) for speed."
    )):

    # Ensure a session_id is provided for multi-turn chat
    if not request.session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="session_id is required for multi-turn chat."
        )

    # Get the generator from the service layer, passing user ID and session ID
    generator = stream_chat_response_with_history(
        user_id=current_user.id, 
        session_id=request.session_id,
        user_message=request.message,
        enable_tools=enable_tools
    )
    
    return StreamingResponse(generator, media_type="text/event-stream")

"""
This part is for the RAG Document Upload
"""
DOCUMENTS_DIR = os.path.join(os.getcwd(), "documents")
os.makedirs(DOCUMENTS_DIR, exist_ok=True) # Create the directory if it doesn't exist

@router.post("/upload-document", summary="Upload a document for RAG indexing")
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Only PDF files are allowed."
        )
    
    # Save the file to the documents directory
    file_path = os.path.join(DOCUMENTS_DIR, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        )

    # Trigger the background indexing task (Step 2)
    index_document_task.delay(file_path, current_user.id)
    
    return {
        "filename": file.filename,
        "message": "Document uploaded successfully. Indexing started in the background."
    }
    