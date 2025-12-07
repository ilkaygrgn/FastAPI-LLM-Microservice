from fastapi import APIRouter, Depends
from app.services import job_service
from app.core.security import get_current_user


router = APIRouter()

@router.post("/start-job", summary="Start a long running background job")
def start_background_job(current_user: dict = Depends(get_current_user)):
    """Triggers an asynchronous background job."""
    result = job_service.start_job()
    return {"message": "Job started", "result": result}
