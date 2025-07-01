import os
import redis
from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
CACHE_EXPIRATION = int(os.getenv("REDIS_TTL_SECONDS", 86400))  # Optional TTL

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    decode_responses=False  # store binary images
)

def get_from_cache(key: str) -> bytes | None:
    try:
        return redis_client.get(key)
    except redis.RedisError as e:
        print(f"[REDIS ERROR] {e}")
        return None

def set_in_cache(key: str, data: bytes, expire: int = CACHE_EXPIRATION):
    try:
        redis_client.setex(key, expire, data)
    except redis.RedisError as e:
        print(f"[REDIS ERROR] {e}")
