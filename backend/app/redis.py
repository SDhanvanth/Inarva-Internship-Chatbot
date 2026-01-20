"""
Redis connection management for caching and rate limiting.
"""
import redis.asyncio as redis
from typing import Optional
from contextlib import asynccontextmanager

from app.config import settings


class RedisManager:
    """Manages Redis connections."""
    
    _instance: Optional["RedisManager"] = None
    _pool: Optional[redis.ConnectionPool] = None
    _client: Optional[redis.Redis] = None
    
    def __new__(cls) -> "RedisManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def connect(self) -> None:
        """Initialize Redis connection pool."""
        if self._pool is None:
            self._pool = redis.ConnectionPool.from_url(
                settings.REDIS_URL,
                max_connections=50,
                decode_responses=True,
            )
            self._client = redis.Redis(connection_pool=self._pool)
    
    async def disconnect(self) -> None:
        """Close Redis connections."""
        if self._client:
            await self._client.close()
        if self._pool:
            await self._pool.disconnect()
        self._pool = None
        self._client = None
    
    @property
    def client(self) -> redis.Redis:
        """Get Redis client."""
        if self._client is None:
            raise RuntimeError("Redis not connected. Call connect() first.")
        return self._client
    
    async def health_check(self) -> bool:
        """Check if Redis is healthy."""
        try:
            await self.client.ping()
            return True
        except Exception:
            return False


# Global Redis manager instance
redis_manager = RedisManager()


async def get_redis() -> redis.Redis:
    """Dependency that provides Redis client."""
    return redis_manager.client


@asynccontextmanager
async def redis_context():
    """Context manager for Redis operations."""
    try:
        yield redis_manager.client
    except Exception:
        raise
