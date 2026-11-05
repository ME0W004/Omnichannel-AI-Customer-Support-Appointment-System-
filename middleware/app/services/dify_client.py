import logging
from typing import Any, Dict, Optional, Tuple
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


class DifyClient:
    def __init__(self):
        self.base_url = settings.DIFY_API_BASE_URL.rstrip("/")
        self.api_key = settings.DIFY_API_KEY
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def chat_message(
        self,
        query: str,
        user_id: str,
        conversation_id: Optional[str] = None,
        inputs: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[str], Optional[str], bool]:
        """
        Sends query to Dify App.
        Returns:
            (answer, dify_conversation_id, handoff_requested)
        """
        url = f"{self.base_url}/chat-messages"
        payload = {
            "inputs": inputs or {},
            "query": query,
            "response_mode": "blocking",
            "user": user_id,
            "auto_generate_name": False,
        }
        if conversation_id:
            payload["conversation_id"] = conversation_id

        try:
            async with httpx.AsyncClient(timeout=settings.DIFY_TIMEOUT_SECONDS) as client:
                res = await client.post(url, json=payload, headers=self.headers)

                if res.status_code != 200:
                    logger.error("Dify API error [%s]: %s", res.status_code, res.text)
                    return None, conversation_id, True  # Trigger handoff on API failure

                data = res.json()
                answer = data.get("answer", "").strip()
                new_conv_id = data.get("conversation_id", conversation_id)

                # Check if Dify explicitly triggered handoff token
                if settings.HANDOFF_TRIGGER_TOKEN in answer:
                    logger.info("Dify emitted handoff token: %s", settings.HANDOFF_TRIGGER_TOKEN)
                    # Clean out the token if any text remains or trigger pure handoff
                    cleaned_answer = answer.replace(settings.HANDOFF_TRIGGER_TOKEN, "").strip()
                    return cleaned_answer or None, new_conv_id, True

                return answer, new_conv_id, False

        except httpx.TimeoutException:
            logger.error("Timeout occurred while contacting Dify.")
            return None, conversation_id, True
        except Exception as e:
            logger.exception("Unexpected error communicating with Dify: %s", e)
            return None, conversation_id, True


dify_client = DifyClient()
