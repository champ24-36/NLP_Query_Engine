import time
import logging
from typing import Any, Optional, Dict, List
from collections import OrderedDict
from datetime import datetime

logger = logging.getLogger(__name__)

class QueryCache:
    """
    In-memory cache for query results with TTL and LRU eviction.
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: OrderedDict = OrderedDict()
        self.hits = 0
        self.misses = 0
        self.recent_queries: List[Dict] = []
        
        logger.info(f"Query cache initialized: max_size={max_size}, default_ttl={default_ttl}s")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve value from cache if exists and not expired.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        if key not in self.cache:
            self.misses += 1
            return None
        
        entry = self.cache[key]
        
        # Check if expired
        if time.time() > entry['expires_at']:
            self.cache.pop(key)
            self.misses += 1
            logger.debug(f"Cache expired for key: {key}")
            return None
        
        # Move to end (most recently used)
        self.cache.move_to_end(key)
        self.hits += 1
        logger.debug(f"Cache hit for key: {key}")
        
        return entry['value']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Store value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default if None)
        """
        if ttl is None:
            ttl = self.default_ttl
        
        # Evict oldest if at capacity
        if len(self.cache) >= self.max_size and key not in self.cache:
            oldest_key = next(iter(self.cache))
            self.cache.pop(oldest_key)
            logger.debug(f"Cache evicted oldest key: {oldest_key}")
        
        self.cache[key] = {
            'value': value,
            'expires_at': time.time() + ttl,
            'created_at': time.time()
        }
        
        # Move to end
        self.cache.move_to_end(key)
        logger.debug(f"Cache set for key: {key}, ttl={ttl}s")
    
    def delete(self, key: str) -> bool:
        """
        Delete a key from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key was deleted, False if not found
        """
        if key in self.cache:
            self.cache.pop(key)
            logger.debug(f"Cache deleted key: {key}")
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
        logger.info("Cache cleared")
    
    def size(self) -> int:
        """Get current cache size."""
        return len(self.cache)
    
    def hit_rate(self) -> float:
        """
        Calculate cache hit rate.
        
        Returns:
            Hit rate as float between 0 and 1
        """
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired entries.
        
        Returns:
            Number of entries removed
        """
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if current_time > entry['expires_at']
        ]
        
        for key in expired_keys:
            self.cache.pop(key)
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': self.hit_rate(),
            'utilization': len(self.cache) / self.max_size if self.max_size > 0 else 0
        }
    
    def add_query_to_history(self, query: str, result: Dict) -> None:
        """
        Add query to recent history.
        
        Args:
            query: Query string
            result: Query result
        """
        self.recent_queries.insert(0, {
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'processing_time': result.get('processing_time', 0),
            'cached': result.get('cached', False),
            'query_type': result.get('query_type', 'unknown')
        })
        
        # Keep only last 100 queries
        self.recent_queries = self.recent_queries[:100]
    
    def get_recent_queries(self, limit: int = 20) -> List[Dict]:
        """
        Get recent queries.
        
        Args:
            limit: Maximum number of queries to return
            
        Returns:
            List of recent queries
        """
        return self.recent_queries[:limit]
