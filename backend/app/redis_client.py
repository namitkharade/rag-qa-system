import json
from typing import Optional

import redis
from app.config import settings


class RedisClient:
    """Redis client for caching ephemeral drawing data with TTL."""
    
    def __init__(self):
        self.client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            decode_responses=True
        )
        self.default_ttl = 3600
    
    def store_drawing(self, user_id: str, drawing_data: list, ttl: Optional[int] = None) -> bool:
        """Store drawing JSON in Redis with TTL."""
        key = f"session:{user_id}:drawing"
        json_str = json.dumps(drawing_data)
        ttl = ttl or self.default_ttl
        
        return self.client.setex(key, ttl, json_str)
    
    def get_drawing(self, user_id: str) -> Optional[list]:
        """Retrieve drawing JSON from Redis."""
        key = f"session:{user_id}:drawing"
        json_str = self.client.get(key)
        
        if json_str:
            return json.loads(json_str)
        return None
    
    def delete_drawing(self, user_id: str) -> bool:
        """Delete drawing data from Redis."""
        key = f"session:{user_id}:drawing"
        return bool(self.client.delete(key))
    
    def get_ttl(self, user_id: str) -> int:
        """Get remaining TTL for drawing data."""
        key = f"session:{user_id}:drawing"
        return self.client.ttl(key)
    
    def ping(self) -> bool:
        """Check Redis connection."""
        try:
            return self.client.ping()
        except Exception:
            return False
    
    def close(self):
        """Close Redis connection."""
        try:
            self.client.close()
        except Exception:
            pass


def get_redis_client() -> RedisClient:
    """FastAPI dependency that provides a Redis client instance."""
    return RedisClient()
