import json
from app.db.redis_client import redis_client
from typing import List, Dict

# Key template for storing history:
HISTORY_KEY = "chat_history:{user_id}:{session_id}"
MAX_HISTORY_LENGTH = 10 # Keep the last 10 messages (5 user, 5 assistant)

def get_session_history(user_id: str, session_id: str) -> List[Dict[str, str]]:
    """Retrieves the chat history for a given user and session from Redis"""
    if not redis_client:
        return []

    key = HISTORY_KEY.format(user_id=user_id, session_id=session_id)
    # LTRIM keeps the history size bounded (short-term memory window)
    history_json = redis_client.lrange(key, -MAX_HISTORY_LENGTH, -1)

    return [json.loads(msg) for msg in history_json]

def add_message_to_history(user_id: str, session_id: str, message: Dict[str, str]):
    """Adds a message to the chat history for a given user and session in Redis"""
    if not redis_client:
        return
    key = HISTORY_KEY.format(user_id=user_id, session_id=session_id)
    # LPUSH adds to the left (head). LTRIM can then easily keep the length bounded.
    redis_client.rpush(key, json.dumps(message))
    # Keep the list size bounded
    redis_client.ltrim(key, -MAX_HISTORY_LENGTH, -1)
