import logging
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

class CacheService:
    """manages gemini context caches for single documents"""

    def __init__(self, gemini_key: str):
        if not gemini_key:
            raise ValueError("gemini_key is required for CacheService. strict BYOK is enabled.")
        self.client = genai.Client(api_key=gemini_key)
        self.model_id = 'models/gemini-2.0-flash'

    def create_document_cache(self, document_text: str, project_id: str, ttl_seconds: int = 3600) -> str:
        """uploads document text to google server and returns cache_name"""
        try:
            logger.info(f"creating context cache for project {project_id} ({len(document_text)} chars)")
            
            cached_content = self.client.caches.create(
                model=self.model_id,
                config=types.CreateCachedContentConfig(
                    contents=[document_text],
                    ttl=f"{ttl_seconds}s",
                    display_name=f"project_{project_id}_cache"
                )
            )
            
            logger.info(f"successfully created cache: {cached_content.name}")
            return cached_content.name
            
        except Exception as e:
            logger.error(f"failed to create context cache: {e}")
            return None

    def get_cache(self, cache_name: str):
        """retrieves cache metadata to verify it exists and is not expired"""
        try:
            return self.client.caches.get(name=cache_name)
        except Exception as e:
            logger.warning(f"cache {cache_name} not found or expired: {e}")
            return None

    def delete_cache(self, cache_name: str):
        """explicitly deletes the cache to save costs"""
        try:
            self.client.caches.delete(name=cache_name)
            logger.info(f"successfully deleted cache: {cache_name}")
        except Exception as e:
            logger.error(f"failed to delete cache {cache_name}: {e}")
