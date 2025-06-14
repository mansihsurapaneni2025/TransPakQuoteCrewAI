import redis
import json
import os
from datetime import datetime, timedelta

class CacheManager:
    """Redis-based caching for quote results and agent responses"""
    
    def __init__(self):
        # Use Redis if available, otherwise fall back to in-memory dict
        try:
            self.redis_client = redis.Redis(
                host=os.environ.get('REDIS_HOST', 'localhost'),
                port=int(os.environ.get('REDIS_PORT', 6379)),
                decode_responses=True
            )
            self.redis_client.ping()
            self.use_redis = True
        except:
            self.cache = {}
            self.use_redis = False
    
    def get_cached_quote(self, shipment_hash):
        """Check if we have a cached quote for similar shipment"""
        if self.use_redis:
            return self.redis_client.get(f"quote:{shipment_hash}")
        return self.cache.get(f"quote:{shipment_hash}")
    
    def cache_quote(self, shipment_hash, quote_data, ttl_hours=24):
        """Cache quote result for future similar requests"""
        key = f"quote:{shipment_hash}"
        data = json.dumps({
            'quote': quote_data,
            'cached_at': datetime.now().isoformat()
        })
        
        if self.use_redis:
            self.redis_client.setex(key, timedelta(hours=ttl_hours), data)
        else:
            self.cache[key] = data
    
    def generate_shipment_hash(self, shipment_info):
        """Generate hash for shipment to check cache"""
        import hashlib
        
        # Create consistent hash from key shipment attributes
        key_data = f"{shipment_info.get('dimensions', '')}-" \
                  f"{shipment_info.get('weight', '')}-" \
                  f"{shipment_info.get('origin', '')}-" \
                  f"{shipment_info.get('destination', '')}-" \
                  f"{shipment_info.get('fragility', '')}"
        
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get_agent_metrics(self):
        """Get performance metrics for AI agents"""
        if self.use_redis:
            return self.redis_client.hgetall("agent_metrics")
        return self.cache.get("agent_metrics", {})
    
    def update_agent_metrics(self, agent_name, processing_time, success=True):
        """Track agent performance metrics"""
        key = "agent_metrics"
        metric_key = f"{agent_name}_avg_time"
        success_key = f"{agent_name}_success_rate"
        
        if self.use_redis:
            current_time = self.redis_client.hget(key, metric_key) or "0"
            current_success = self.redis_client.hget(key, success_key) or "100"
            
            # Simple moving average
            new_time = (float(current_time) + processing_time) / 2
            new_success = (float(current_success) + (100 if success else 0)) / 2
            
            self.redis_client.hset(key, metric_key, str(new_time))
            self.redis_client.hset(key, success_key, str(new_success))
        else:
            if key not in self.cache:
                self.cache[key] = {}
            
            current_time = float(self.cache[key].get(metric_key, 0))
            new_time = (current_time + processing_time) / 2
            self.cache[key][metric_key] = str(new_time)