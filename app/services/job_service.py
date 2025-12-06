# app/services/job_service.py
from app.workers.worker import run_long_task
import uuid

def start_job():
    """Start a new job"""
    task_id = str(uuid.uuid4())
    # .delay() is a Celery method that schedules the task to run asynchronously
    task = run_long_task.delay(task_id)
    return {"task_id": task_id, "status": "PENDING"}