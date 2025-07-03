from cachetools import LRUCache

local_cache = LRUCache(maxsize=100)

def get_from_memory_cache(key: str) -> bytes | None:
    return local_cache.get(key)

def set_in_memory_cache(key: str, data: bytes):
    local_cache[key] = data
