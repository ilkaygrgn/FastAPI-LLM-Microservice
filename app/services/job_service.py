# app/services/job_service.py
def enqueue_job_stub(payload: dict) -> dict:
    """
    Enqueue a long-running job (stub).
    Replace with Redis/RQ or Celery implementation later.
    """
    # return a fake job id and status for now
    return {"job_id": "stub-1234", "status": "enqueued"}