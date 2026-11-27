import json
import logging
from functools import lru_cache
from typing import Any, Dict, Optional

from google.cloud import tasks_v2
from google.protobuf import duration_pb2

from core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# cloud tasks caps http handlers at 30 min and retries past the deadline, so a
# slower job would be dispatched twice. workers must finish inside this window.
DISPATCH_DEADLINE_SECONDS = 1800


class CloudTasksService:
    """publishes worker tasks to a cloud tasks queue"""

    def __init__(self):
        self._client = tasks_v2.CloudTasksClient()
        self._queue_path = self._client.queue_path(
            settings.GCP_PROJECT_ID,
            settings.CLOUD_TASKS_LOCATION,
            settings.CLOUD_TASKS_QUEUE,
        )

    def publish_task(self, destination_url: str, payload: Dict[str, Any]) -> str:
        """publish json payload to worker url, returning the task name"""
        http_request = tasks_v2.HttpRequest(
            http_method=tasks_v2.HttpMethod.POST,
            url=destination_url,
            headers={"Content-Type": "application/json"},
            body=json.dumps(payload).encode(),
        )

        # oidc lets the worker prove the caller is this queue, not the public internet
        if settings.CLOUD_TASKS_INVOKER_SA:
            http_request.oidc_token = tasks_v2.OidcToken(
                service_account_email=settings.CLOUD_TASKS_INVOKER_SA,
                audience=destination_url,
            )

        task = tasks_v2.Task(
            http_request=http_request,
            dispatch_deadline=duration_pb2.Duration(seconds=DISPATCH_DEADLINE_SECONDS),
        )

        try:
            created = self._client.create_task(
                request=tasks_v2.CreateTaskRequest(parent=self._queue_path, task=task)
            )
            return created.name
        except Exception as e:
            raise Exception(f"cloud tasks publish failed: {str(e)}")


@lru_cache(maxsize=1)
def get_queue_service() -> Optional[CloudTasksService]:
    """cached: each CloudTasksClient opens its own grpc channel"""
    if settings.GCP_PROJECT_ID and settings.CLOUD_TASKS_QUEUE:
        logger.info("initializing cloud tasks queue service")
        return CloudTasksService()

    logger.info("cloud tasks not configured, running without external queue")
    return None
