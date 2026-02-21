from upstash_redis import Redis
from core.config import get_settings
from typing import Dict, Any, Optional
import json
import time

settings = get_settings()

class UpstashJobService:
    """
    manages async job state in upstash redis
    keys stored as 'jobs:{job_id}'
    """
    
    def __init__(self):
        from upstash_redis import Redis
        self.redis = Redis(
            url=settings.UPSTASH_REDIS_REST_URL,
            token=settings.UPSTASH_REDIS_REST_TOKEN
        )
        self.ttl = 86400  # 24 hours retention

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
        
        # use hash for efficient field-level updates
        key = f"jobs:{job_id}"
        self.redis.hset(key, values=job_data)
        self.redis.expire(key, self.ttl)
        
        return job_data

    def update_metadata(self, job_id: str, updates: Dict[str, Any]):
        """update or merge job metadata"""
        key = f"jobs:{job_id}"
        current_job = self.get_job(job_id)
        if not current_job:
            return
            
        metadata = current_job.get("metadata", {})
        metadata.update(updates)
        
        self.redis.hset(key, "metadata", json.dumps(metadata))
        self.redis.hset(key, "updated_at", int(time.time()))

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

    def set_extraction_cache(self, job_id: str, data: Any):
        """cache raw extraction results (expensive part)"""
        key = f"jobs:{job_id}:cache"
        self.redis.set(key, json.dumps(data), ex=self.ttl)
        print(f"[JOB_SERVICE] cached extraction results for job {job_id}")

    def get_extraction_cache(self, job_id: str) -> Optional[Any]:
        """retrieve cached extraction results if available"""
        key = f"jobs:{job_id}:cache"
        cached = self.redis.get(key)
        if cached:
            print(f"[JOB_SERVICE] found cached extraction results for job {job_id}")
            return json.loads(cached)
        return None

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """get job details"""
        key = f"jobs:{job_id}"
        data = self.redis.hgetall(key)
        
        if not data:
            return None
            
        # parse json fields
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


class LocalJobService:
    """
    in-memory job state manager for local development
    used when upstash redis keys are omitted
    """
    
    # class-level dict to persist across request lifecycles during local dev runs
    _mem_store: Dict[str, Dict[str, Any]] = {}
    _cache_store: Dict[str, Any] = {}
    
    def __init__(self):
        self.store = self.__class__._mem_store
        self.cache = self.__class__._cache_store

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
        
        self.store[job_id] = job_data
        return job_data

    def update_metadata(self, job_id: str, updates: Dict[str, Any]):
        """update or merge job metadata"""
        if job_id not in self.store:
            return
            
        # unmarshall, update, and stringify metadata dict back
        metadata_str = self.store[job_id].get("metadata", "{}")
        try:
            metadata = json.loads(metadata_str)
        except:
            metadata = {}
            
        metadata.update(updates)
        self.store[job_id]["metadata"] = json.dumps(metadata)
        self.store[job_id]["updated_at"] = int(time.time())

    def update_progress(self, job_id: str, status: str, progress: int = None, details: Dict[str, Any] = None):
        """update job progress and status"""
        if job_id not in self.store:
            return
            
        self.store[job_id]["status"] = status
        self.store[job_id]["updated_at"] = int(time.time())
        
        if progress is not None:
            self.store[job_id]["progress"] = progress
            
        if details and status in ["completed", "failed"]:
            self.store[job_id]["result"] = json.dumps(details)

    def set_extraction_cache(self, job_id: str, data: Any):
        """cache raw extraction results (expensive part)"""
        self.cache[job_id] = json.dumps(data)
        print(f"[LOCAL_JOB_SERVICE] cached extraction results for job {job_id}")

    def get_extraction_cache(self, job_id: str) -> Optional[Any]:
        """retrieve cached extraction results if available"""
        cached = self.cache.get(job_id)
        if cached:
            print(f"[LOCAL_JOB_SERVICE] found cached extraction results for job {job_id}")
            return json.loads(cached)
        return None

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """get job details"""
        if job_id not in self.store:
            return None
            
        # create a copy to avoid mutating the in-memory store reference while parsing
        data = self.store[job_id].copy()
            
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


def get_job_service():
    """factory function to return Upstash if configured, otherwise Local in-memory"""
    if settings.UPSTASH_REDIS_REST_URL and settings.UPSTASH_REDIS_REST_TOKEN:
        import logging
        logging.getLogger(__name__).info("initializing upstash job service")
        return UpstashJobService()
    else:
        import logging
        logging.getLogger(__name__).info("upstash credentials missing, falling back to local memory job service")
        return LocalJobService()
