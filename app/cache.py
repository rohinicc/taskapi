import os
import json
import logging

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
TTL = 300  # 5 minutes

class _RedisClient:
    def __init__(self):
        self._client = None

    def _connect(self):
        if self._client is not None:
            return
        try:
            import redis
            self._client = redis.from_url(REDIS_URL, decode_responses=True)
            self._client.ping()
        except Exception:
            self._client = None
            logger.warning("Redis unavailable — caching disabled")

    @property
    def available(self):
        self._connect()
        return self._client is not None

    def get(self, key):
        self._connect()
        if not self._client:
            return None
        return self._client.get(key)

    def setex(self, key, ttl, value):
        self._connect()
        if self._client:
            self._client.setex(key, ttl, value)

    def delete(self, key):
        self._connect()
        if self._client:
            self._client.delete(key)

    def scan_iter(self, pattern):
        self._connect()
        if not self._client:
            return iter([])
        return self._client.scan_iter(pattern)

_r = _RedisClient()

def get_cached(key: str):
    val = _r.get(key)
    return json.loads(val) if val else None

def set_cached(key: str, data):
    _r.setex(key, TTL, json.dumps(data, default=str))

def delete_cached(key: str):
    _r.delete(key)

def flush_tasks():
    for key in _r.scan_iter("task:*"):
        _r.delete(key)
