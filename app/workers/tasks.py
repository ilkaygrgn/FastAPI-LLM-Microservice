# app/workers/tasks.py

import time
from app.workers.worker import celery_app
from app.services.chat_history import get_session_history
from app.core.config import settings
from app.db.database import SessionLocal
from app.models.user import User
from google import genai


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