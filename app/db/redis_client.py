import redis
from app.core.config import settings

# Initialize Redis client using the URL from the config
try:
    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=int(settings.REDIS_PORT),
        db=0,
        decode_responses=True,
    )
    # Test the connection
    redis_client.ping()
    print("Redis connection successful")
except Exception as e:
    print(f"Redis connection failed: {e}")
    redis_client = None
