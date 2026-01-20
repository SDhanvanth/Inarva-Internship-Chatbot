"""
Rate limiting using Redis.
"""
import time
from typing import Optional, Tuple
from redis import Redis

from app.config import settings


class RateLimiter:
    """
    Redis-based rate limiter using sliding window algorithm.
    """
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
    
    async def is_allowed(
        self,
        key: str,
        limit: int,
        window_seconds: int
    ) -> Tuple[bool, dict]:
        """
        Check if request is allowed under rate limit.
        
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        now = time.time()
        window_start = now - window_seconds
        
        # Use Redis pipeline for atomic operations
        pipe = self.redis.pipeline()
        
        # Remove old entries outside the window
        pipe.zremrangebyscore(key, 0, window_start)
        
        # Count current requests in window
        pipe.zcard(key)
        
        # Add current request
        pipe.zadd(key, {str(now): now})
        
        # Set expiry on the key
        pipe.expire(key, window_seconds + 1)
        
        results = await pipe.execute()
        current_count = results[1]
        
        info = {
            "limit": limit,
            "remaining": max(0, limit - current_count - 1),
            "reset": int(now + window_seconds),
            "window": window_seconds
        }
        
        if current_count >= limit:
            # Remove the request we just added since it's over limit
            await self.redis.zrem(key, str(now))
            return False, info
        
        return True, info
    
    async def check_ip_limit(self, ip_address: str) -> Tuple[bool, dict]:
        """Check rate limit for IP address."""
        # Check per-minute limit
        key_minute = f"ratelimit:ip:{ip_address}:minute"
        allowed, info = await self.is_allowed(
            key_minute,
            settings.RATE_LIMIT_IP_PER_MINUTE,
            60
        )
        if not allowed:
            return False, info
        
        # Check per-hour limit
        key_hour = f"ratelimit:ip:{ip_address}:hour"
        allowed, info = await self.is_allowed(
            key_hour,
            settings.RATE_LIMIT_IP_PER_HOUR,
            3600
        )
        return allowed, info
    
    async def check_user_limit(self, user_id: str) -> Tuple[bool, dict]:
        """Check rate limit for authenticated user."""
        # Check per-minute limit
        key_minute = f"ratelimit:user:{user_id}:minute"
        allowed, info = await self.is_allowed(
            key_minute,
            settings.RATE_LIMIT_USER_PER_MINUTE,
            60
        )
        if not allowed:
            return False, info
        
        # Check per-hour limit
        key_hour = f"ratelimit:user:{user_id}:hour"
        allowed, info = await self.is_allowed(
            key_hour,
            settings.RATE_LIMIT_USER_PER_HOUR,
            3600
        )
        return allowed, info
    
    async def check_tool_limit(
        self,
        tool_id: str,
        user_id: str
    ) -> Tuple[bool, dict]:
        """Check rate limit for tool invocations."""
        key = f"ratelimit:tool:{tool_id}:user:{user_id}:minute"
        return await self.is_allowed(
            key,
            settings.RATE_LIMIT_TOOL_PER_MINUTE,
            60
        )
    
    async def get_usage(self, key: str, window_seconds: int) -> int:
        """Get current usage count for a rate limit key."""
        now = time.time()
        window_start = now - window_seconds
        
        # Clean old entries
        await self.redis.zremrangebyscore(key, 0, window_start)
        
        # Count current
        return await self.redis.zcard(key)


class TokenBucket:
    """
    Token bucket algorithm for burst protection.
    """
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
    
    async def consume(
        self,
        key: str,
        tokens: int = 1,
        bucket_size: int = None,
        refill_rate: float = 1.0
    ) -> Tuple[bool, int]:
        """
        Consume tokens from bucket.
        
        Args:
            key: Bucket identifier
            tokens: Number of tokens to consume
            bucket_size: Max bucket capacity
            refill_rate: Tokens per second to refill
            
        Returns:
            Tuple of (success, remaining_tokens)
        """
        bucket_size = bucket_size or settings.RATE_LIMIT_BURST_SIZE
        now = time.time()
        
        bucket_key = f"bucket:{key}"
        last_update_key = f"bucket:{key}:last"
        
        # Get current state
        pipe = self.redis.pipeline()
        pipe.get(bucket_key)
        pipe.get(last_update_key)
        results = await pipe.execute()
        
        current_tokens = float(results[0] or bucket_size)
        last_update = float(results[1] or now)
        
        # Calculate tokens to add based on time elapsed
        elapsed = now - last_update
        tokens_to_add = elapsed * refill_rate
        current_tokens = min(bucket_size, current_tokens + tokens_to_add)
        
        # Try to consume
        if current_tokens >= tokens:
            new_tokens = current_tokens - tokens
            pipe = self.redis.pipeline()
            pipe.set(bucket_key, new_tokens)
            pipe.set(last_update_key, now)
            pipe.expire(bucket_key, 3600)
            pipe.expire(last_update_key, 3600)
            await pipe.execute()
            return True, int(new_tokens)
        
        return False, int(current_tokens)
