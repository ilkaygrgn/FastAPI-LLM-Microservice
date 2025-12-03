from fastapi import FastAPI
from app.db import models
from app.db.database import engine
from app.api.v1 import auth, users, llm, jobs

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="FastAPI LLM Microservice", version="0.1.0")

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(llm.router, prefix="/api/v1/llm", tags=["llm"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["jobs"])


@app.get("/")
def read_root():
    return {"status": "ok", "service": "FastAPI LLM Microservice"}