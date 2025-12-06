# app/workers/worker.py

from celery import Celery
from app.core.config import settings
import time

# Initialize Celery
celery_app = Celery(
    "tasks", # Celery app name
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Example Task
@celery_app.task(name="job_service.run_long_task")
def run_long_task(task_id: str, duration: int = 5):
    """Simulates a long-running process."""
    print(f"Starting task {task_id}. Will run for {duration} seconds.")
    time.sleep(duration)
    result = f"Task {task_id} completed successfully after {duration}s."
    print(result)
    return result