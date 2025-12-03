# app/workers/worker.py
"""
Worker entrypoint for background jobs (RQ / Celery).
When you implement RQ, this file can hold helper job functions the worker imports.
"""
def run_long_task(data):
    # placeholder for a long-running task (e.g., long summarization)
    return {"result": "done", "input_length": len(data.get("text", ""))}