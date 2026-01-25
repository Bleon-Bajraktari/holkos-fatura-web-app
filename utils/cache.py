"""
Sistem caching për optimizim të performancës
"""
from functools import lru_cache
from datetime import datetime, timedelta

class Cache:
    """Klasa për menaxhimin e cache-it"""
    
    _cache = {}
    _cache_times = {}
    _default_ttl = 300  # 5 minuta default
    
    @staticmethod
    def get(key):
        """Merr vlerë nga cache"""
        if key in Cache._cache:
            # Kontrollo nëse ka skaduar
            if key in Cache._cache_times:
                if datetime.now() > Cache._cache_times[key]:
                    # Ka skaduar, fshi
                    del Cache._cache[key]
                    del Cache._cache_times[key]
                    return None
            return Cache._cache[key]
        return None
    
    @staticmethod
    def set(key, value, ttl=None):
        """Vendos vlerë në cache"""
        Cache._cache[key] = value
        ttl = ttl or Cache._default_ttl
        Cache._cache_times[key] = datetime.now() + timedelta(seconds=ttl)
    
    @staticmethod
    def clear(key=None):
        """Pastron cache"""
        if key:
            if key in Cache._cache:
                del Cache._cache[key]
            if key in Cache._cache_times:
                del Cache._cache_times[key]
        else:
            Cache._cache.clear()
            Cache._cache_times.clear()
    
    @staticmethod
    def invalidate_pattern(pattern):
        """Fshi çelësat që përputhen me pattern"""
        keys_to_delete = [k for k in Cache._cache.keys() if pattern in k]
        for key in keys_to_delete:
            Cache.clear(key)

