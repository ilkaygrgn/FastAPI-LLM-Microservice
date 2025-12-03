# app/services/llm_service.py
from app.core.config import settings

def summarize_text_stub(text: str) -> str:
    """
    Temporary local summarizer used while building the app.
    Replace with real OpenAI/SDK call later.
    """
    if not text:
        return ""
    # very simple “summary”: first 200 characters + ellipsis
    return text[:200] + ("..." if len(text) > 200 else "")