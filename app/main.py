from fastapi import FastAPI
from app.db import models
from app.db.database import engine
from app.api.v1 import auth, users, llm, jobs
from sqlalchemy.exc import OperationalError, IntegrityError

app = FastAPI(title="FastAPI LLM Microservice", version="0.1.0")

@app.on_event("startup")
async def startup_event():
    """Create database tables on startup if they don't exist."""
    try:
        models.Base.metadata.create_all(bind=engine, checkfirst=True)
    except (OperationalError, IntegrityError):
        # Tables might already exist or another worker is creating them, which is fine
        pass

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(llm.router, prefix="/api/v1/llm", tags=["llm"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["jobs"])



@app.get("/")
def read_root():
    return {"status": "ok", "service": "FastAPI LLM Microservice"}