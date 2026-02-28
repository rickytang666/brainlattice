import logging
from core.config import get_settings
from typing import Dict, Any, Optional

settings = get_settings()

class QStashService:
    """
    publishes tasks to qstash for async processing
    """
    
    def __init__(self):
        from qstash import QStash
        self.client = QStash(token=settings.QSTASH_TOKEN)

    def publish_task(self, destination_url: str, payload: Dict[str, Any]) -> str:
        """
        publish json payload to worker url
        returns message id
        """
        try:
            result = self.client.message.publish_json(
                url=destination_url,
                body=payload,
                retries=3
            )
            return result.message_id
            
        except Exception as e:
            raise Exception(f"qstash publish failed: {str(e)}")

def get_queue_service() -> Optional[QStashService]:
    """returns qstash service if configured, else none for local fallback"""
    if settings.QSTASH_TOKEN:
        logging.getLogger(__name__).info("initializing qstash queue service")
        return QStashService()
    else:
        logging.getLogger(__name__).info("qstash token missing, running without external queue")
        return None
