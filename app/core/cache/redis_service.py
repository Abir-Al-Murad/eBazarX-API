import json
from typing import Optional, Any, Dict, List, Union, Set
from app.core.redis import redis_client


class RedisService:
    """Service for interacting with Redis cache."""
    
    def __init__(self):
        self.client = redis_client

    # ============================================================
    # Basic Operations
    # ============================================================

    async def get(self, key: str) -> Optional[str]:
        """Get a string value from Redis."""
        return await self.client.get(key)  # type: ignore

    async def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a JSON value from Redis."""
        value = await self.client.get(key)  # type: ignore
        if value:
            return json.loads(value)
        return None

    async def set(
        self,
        key: str,
        value: Union[str, Dict, List],
        ttl: Optional[int] = None,
    ) -> bool:
        """Set a value in Redis with optional TTL (in seconds)."""
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        return await self.client.set(key, value, ex=ttl)  # type: ignore

    async def delete(self, key: str) -> int:
        """Delete a key from Redis."""
        return await self.client.delete(key)  # type: ignore

    async def exists(self, key: str) -> bool:
        """Check if a key exists in Redis."""
        return (await self.client.exists(key)) > 0  # type: ignore

    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration time for a key."""
        return await self.client.expire(key, ttl)  # type: ignore

    async def ttl(self, key: str) -> int:
        """Get remaining TTL of a key in seconds."""
        return await self.client.ttl(key)  # type: ignore

    # ============================================================
    # Hash Operations
    # ============================================================

    async def hget(self, key: str, field: str) -> Optional[str]:
        """Get a field from a hash."""
        return await self.client.hget(key, field)  # type: ignore

    async def hset(self, key: str, field: str, value: str) -> int:
        """Set a field in a hash."""
        return await self.client.hset(key, field, value)  # type: ignore

    async def hgetall(self, key: str) -> Dict[str, str]:
        """Get all fields from a hash."""
        result = await self.client.hgetall(key) # type: ignore
        return dict(result) if result else {}

    async def hdel(self, key: str, *fields: str) -> int:
        """Delete fields from a hash."""
        return await self.client.hdel(key, *fields)  # type: ignore

    # ============================================================
    # Set Operations
    # ============================================================

    async def sadd(self, key: str, *values: str) -> int:
        """Add members to a set."""
        return await self.client.sadd(key, *values)  # type: ignore

    async def srem(self, key: str, *values: str) -> int:
        """Remove members from a set."""
        return await self.client.srem(key, *values)  # type: ignore

    async def sismember(self, key: str, value: str) -> bool:
        """Check if a value is a member of a set."""
        return await self.client.sismember(key, value)  # type: ignore

    async def smembers(self, key: str) -> List[str]:
        """Get all members of a set."""
        members = await self.client.smembers(key)  # type: ignore
        return list(members) if members else []

    # ============================================================
    # Counter Operations
    # ============================================================

    async def incr(self, key: str, amount: int = 1) -> int:
        """Increment a counter."""
        return await self.client.incr(key, amount)  # type: ignore

    async def decr(self, key: str, amount: int = 1) -> int:
        """Decrement a counter."""
        return await self.client.decr(key, amount)  # type: ignore

    # ============================================================
    # Utility
    # ============================================================

    async def ping(self) -> bool:
        """Check if Redis is responsive."""
        try:
            return await self.client.ping()  # type: ignore
        except Exception:
            return False

    async def flush_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern."""
        keys = await self.client.keys(pattern)  # type: ignore
        if keys:
            return await self.client.delete(*keys)  # type: ignore
        return 0


# Singleton instance
redis_service = RedisService()