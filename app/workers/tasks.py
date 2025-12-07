# app/workers/tasks.py

import time
import os
from app.workers.worker import celery_app
from app.services.chat_history import get_session_history
from app.core.config import settings
from app.db.database import SessionLocal
from app.models.user import User
from google import genai

from celery import shared_task
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.services.vector_db_service import save_chunk_to_vector_db



def get_genai_client():
    """Lazy initialization of genai client."""
    return genai.Client(api_key=settings.GOOGLE_API_KEY)


@celery_app.task(name="update_user_profile")
def update_user_profile_task(user_id: str, session_id: str):
    """Background task: Analyze user conversation and update profile."""

    raw_history = get_session_history(user_id, session_id)

    conversation_text = "\n".join(
        f"{msg['role'].title()}: {msg['content']}"
        for msg in raw_history
    )

    prompt = f"""
    Analyze the following conversation and extract 3–5 long-term facts about the user.
    Return one concise paragraph describing the user's long-term profile.

    Conversation:
    {conversation_text}
    """

    try:
        client = get_genai_client()
        response = client.models.generate_content(
            model=settings.GOOGLE_LLM_MODEL,
            contents=[{
                "role": "user",
                "parts": [{"text": prompt}]
            }]
        )
        new_profile = response.text.strip()
    except Exception as e:
        print(f"[ERROR] Gemini failed: {e}")
        return

    # Save to DB
    with SessionLocal() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.user_profile = new_profile
            db.commit()
            print(f"[INFO] Updated user profile for {user_id}")



# Example Task
@celery_app.task(name="job_service.run_long_task")
def run_long_task(task_id: str, duration: int = 5):
    """Simulates a long-running process."""
    print(f"Starting task {task_id}. Will run for {duration} seconds.")
    time.sleep(duration)
    result = f"Task {task_id} completed successfully after {duration}s."
    print(result)
    return result



"""
This part is for the RAG Document Indexing TASK
"""

@shared_task(name="index_document_task")
def index_document_task(file_path: str, user_id: str):
    # --- 1. Load the Document ---
    try:
        loader = PyPDFLoader(file_path)
        documents = loader.load()
    except Exception as e:
        print(f"[ERROR] Failed to load document: {e}")
        return

    # --- 2. Chunking Strategies ---
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    
    chunks = text_splitter.split_documents(documents)

    # --- 3. Embeddings and Vector Store
    # Before saving, inject metadata (user_id) into each chunk
    # This is CRITICAL for user-specific RAG (ensuring one user only searches their own docs)
    for chunk in chunks:
        # LangChain stores metadata as a dictionary in the 'metadata' attribute
        chunk.metadata["user_id"] = user_id
        chunk.metadata["source"] = os.path.basename(file_path)
        
    try:
        # Call the service function to generate embeddings and save to vector DB
        save_chunk_to_vector_db(chunks)
        print("Successfully saved chunks to vector store.")
        
    except Exception as e:
        print(f"FATAL ERROR during PGVector storage: {e}")
        # Log the error but continue to clean up the file

    # --- 4. Clean up
    os.remove(file_path)
    print(f"Indexing complete. Removed file: {file_path}")
