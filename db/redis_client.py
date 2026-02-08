"""
Redis Connection Client for HabitatOS V2 Memory System.
Provides singleton Redis client for session and procedural memory storage.
"""

import os
import redis
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")


class RedisClient:
    """
    Singleton Redis client for memory operations.
    Used for procedural memory and session management.
    """

    _instance: Optional[redis.Redis] = None

    @classmethod
    def get_client(cls) -> redis.Redis:
        """
        Get or create Redis client singleton.
        
        Returns:
            redis.Redis: Connected Redis client
        """
        if cls._instance is None:
            cls._instance = redis.from_url(
                REDIS_URL,
                decode_responses=True,  # Return strings instead of bytes
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )
            # Test connection
            try:
                cls._instance.ping()
            except redis.ConnectionError as e:
                raise ConnectionError(f"Failed to connect to Redis at {REDIS_URL}: {e}")
        
        return cls._instance

    @classmethod
    def close(cls) -> None:
        """Close the Redis connection."""
        if cls._instance is not None:
            cls._instance.close()
            cls._instance = None


# Convenience function
def get_redis() -> redis.Redis:
    """Get Redis client instance."""
    return RedisClient.get_client()
