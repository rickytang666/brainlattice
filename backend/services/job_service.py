from upstash_redis import Redis
from core.config import get_settings
from typing import Dict, Any, Optional
import json
import time

settings = get_settings()

class JobService:
    """
    manages async job state in upstash redis.
    keys are stored as 'jobs:{job_id}'.
    """
    
    def __init__(self):
        self.redis = Redis(
            url=settings.UPSTASH_REDIS_REST_URL,
            token=settings.UPSTASH_REDIS_REST_TOKEN
        )
        self.ttl = 86400 # 24 hours retention

    def create_job(self, job_id: str, job_type: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """initialize a new job"""
        now = int(time.time())
        job_data = {
            "id": job_id,
            "type": job_type,
            "status": "pending",
            "progress": 0,
            "created_at": now,
            "updated_at": now,
            "metadata": json.dumps(metadata or {})
        }
        
        # use hash for field-level updates
        key = f"jobs:{job_id}"
        self.redis.hset(key, values=job_data)
        self.redis.expire(key, self.ttl)
        
        return job_data

    def update_progress(self, job_id: str, status: str, progress: int = None, details: Dict[str, Any] = None):
        """update job progress and status"""
        key = f"jobs:{job_id}"
        
        updates = {
            "status": status,
            "updated_at": int(time.time())
        }
        
        if progress is not None:
            updates["progress"] = progress
            
        if details:
            if status in ["completed", "failed"]:
                updates["result"] = json.dumps(details)
        
        self.redis.hset(key, values=updates)

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """get job details"""
        key = f"jobs:{job_id}"
        data = self.redis.hgetall(key)
        
        if not data:
            return None
            
        # parse json fields back
        if "metadata" in data and isinstance(data["metadata"], str):
            try:
                data["metadata"] = json.loads(data["metadata"])
            except:
                pass
                
        if "result" in data and isinstance(data["result"], str):
            try:
                data["result"] = json.loads(data["result"])
            except:
                pass
                
        return data
