import json
import redis
from typing import Optional
from abc import ABC, abstractmethod
from .models import MemorySnapshot
from .config import settings


class MemoryStore(ABC):
    """Abstract base class for memory persistence"""
    
    @abstractmethod
    async def save(self, session_id: str, snapshot: MemorySnapshot):
        """Save memory snapshot"""
        pass
    
    @abstractmethod
    async def load(self, session_id: str) -> Optional[MemorySnapshot]:
        """Load memory snapshot"""
        pass
    
    @abstractmethod
    async def delete(self, session_id: str):
        """Delete memory snapshot"""
        pass
    
    @abstractmethod
    async def list_sessions(self) -> list[str]:
        """List all session IDs"""
        pass


class InMemoryStore(MemoryStore):
    """In-memory storage for development/testing"""
    
    def __init__(self):
        self.storage: dict[str, MemorySnapshot] = {}
    
    async def save(self, session_id: str, snapshot: MemorySnapshot):
        """Save to memory"""
        snapshot.update_timestamp()
        self.storage[session_id] = snapshot
    
    async def load(self, session_id: str) -> Optional[MemorySnapshot]:
        """Load from memory"""
        return self.storage.get(session_id)
    
    async def delete(self, session_id: str):
        """Delete from memory"""
        if session_id in self.storage:
            del self.storage[session_id]
    
    async def list_sessions(self) -> list[str]:
        """List session IDs"""
        return list(self.storage.keys())


class RedisStore(MemoryStore):
    """Redis-based persistent storage"""
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            password=settings.redis_password,
            decode_responses=True
        )
        self.key_prefix = "agent_memory:"
    
    def _get_key(self, session_id: str) -> str:
        """Generate Redis key"""
        return f"{self.key_prefix}{session_id}"
    
    async def save(self, session_id: str, snapshot: MemorySnapshot):
        """Save to Redis"""
        snapshot.update_timestamp()
        key = self._get_key(session_id)
        data = snapshot.model_dump_json()
        
        # Save with 7 day expiration
        self.redis_client.setex(key, 604800, data)
    
    async def load(self, session_id: str) -> Optional[MemorySnapshot]:
        """Load from Redis"""
        key = self._get_key(session_id)
        data = self.redis_client.get(key)
        
        if data:
            return MemorySnapshot.model_validate_json(data)
        return None
    
    async def delete(self, session_id: str):
        """Delete from Redis"""
        key = self._get_key(session_id)
        self.redis_client.delete(key)
    
    async def list_sessions(self) -> list[str]:
        """List session IDs"""
        pattern = f"{self.key_prefix}*"
        keys = self.redis_client.keys(pattern)
        return [key.replace(self.key_prefix, "") for key in keys]


def get_memory_store() -> MemoryStore:
    """Factory function to get appropriate memory store"""
    if settings.use_redis:
        try:
            return RedisStore()
        except Exception as e:
            print(f"Redis connection failed: {e}. Falling back to in-memory storage.")
            return InMemoryStore()
    else:
        return InMemoryStore()
