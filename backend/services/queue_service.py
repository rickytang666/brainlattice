from qstash import QStash
from core.config import get_settings
from typing import Dict, Any

settings = get_settings()

class QStashService:
    """
    publishes tasks to qstash for async processing
    """
    
    def __init__(self):
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
