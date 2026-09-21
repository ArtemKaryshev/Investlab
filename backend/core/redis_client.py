import json
import redis.asyncio as aioredis
from typing import Optional, Any
from .config import settings


class RedisClient:
    """Redis client for caching and rate limiting."""
    
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
    
    async def connect(self):
        """Connect to Redis."""
        self.redis = await aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.redis:
            return None
        
        value = await self.redis.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None
    
    async def set(self, key: str, value: Any, expire: int = 3600) -> bool:
        """Set value in cache with expiration."""
        if not self.redis:
            return False
        
        if not isinstance(value, str):
            value = json.dumps(value)
        
        return await self.redis.set(key, value, ex=expire)
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.redis:
            return False
        return await self.redis.delete(key) > 0
    
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        if not self.redis:
            return False
        return await self.redis.exists(key) > 0
    
    async def incr(self, key: str, expire: Optional[int] = None) -> int:
        """Increment counter."""
        if not self.redis:
            return 0
        
        value = await self.redis.incr(key)
        if expire and value == 1:
            await self.redis.expire(key, expire)
        return value


# Global Redis client instance
redis_client = RedisClient()
