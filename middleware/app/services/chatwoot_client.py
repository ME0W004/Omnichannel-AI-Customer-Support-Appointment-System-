import logging
from typing import List, Optional
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


class ChatwootClient:
    def __init__(self):
        self.base_url = settings.CHATWOOT_BASE_URL.rstrip("/")
        self.account_id = settings.CHATWOOT_ACCOUNT_ID
        self.headers = {
            "api_access_token": settings.CHATWOOT_API_ACCESS_TOKEN,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    @property
    def api_prefix(self) -> str:
        return f"{self.base_url}/api/v1/accounts/{self.account_id}"

    async def send_message(
        self,
        conversation_id: int,
        content: str,
        message_type: str = "outgoing",
        private: bool = False,
    ) -> bool:
        """Send message or private note to a conversation in Chatwoot."""
        url = f"{self.api_prefix}/conversations/{conversation_id}/messages"
        payload = {
            "content": content,
            "message_type": message_type,
            "private": private,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, json=payload, headers=self.headers)
                if res.status_code in (200, 201):
                    logger.info(
                        "Message sent to Chatwoot conversation %s (private=%s)",
                        conversation_id,
                        private,
                    )
                    return True
                logger.error(
                    "Failed to send message to Chatwoot [%s]: %s",
                    res.status_code,
                    res.text,
                )
                return False
        except Exception as e:
            logger.exception("Exception in Chatwoot send_message: %s", e)
            return False

    async def add_labels(self, conversation_id: int, labels: List[str]) -> bool:
        """Add tags/labels to a conversation."""
        url = f"{self.api_prefix}/conversations/{conversation_id}/labels"
        payload = {"labels": labels}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, json=payload, headers=self.headers)
                return res.status_code in (200, 201)
        except Exception as e:
            logger.exception("Exception in Chatwoot add_labels: %s", e)
            return False

    async def unassign_bot(self, conversation_id: int) -> bool:
        """
        Unassign any bot/agent so it lands in the general human queue
        or assign to human team.
        """
        url = f"{self.api_prefix}/conversations/{conversation_id}/assignments"
        payload = {"assignee_id": None}
        if settings.HANDOFF_ASSIGNED_TEAM_ID > 0:
            payload["team_id"] = settings.HANDOFF_ASSIGNED_TEAM_ID

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, json=payload, headers=self.headers)
                return res.status_code in (200, 201)
        except Exception as e:
            logger.exception("Exception in Chatwoot unassign_bot: %s", e)
            return False

    async def toggle_status(self, conversation_id: int, status: str = "open") -> bool:
        """Change conversation status (e.g. 'open' to ensure human visibility)."""
        url = f"{self.api_prefix}/conversations/{conversation_id}/toggle_status"
        payload = {"status": status}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, json=payload, headers=self.headers)
                return res.status_code in (200, 201)
        except Exception as e:
            logger.exception("Exception in Chatwoot toggle_status: %s", e)
            return False

    async def trigger_human_handoff(
        self, conversation_id: int, reason: str, user_notice: Optional[str] = None
    ) -> bool:
        """
        Execute full Zero-Fail Human Handoff workflow:
        1. Add handoff label (e.g. human-needed)
        2. Set conversation to open/unassigned
        3. Post private staff note explaining the exact trigger
        4. Send polite transition message to user
        """
        logger.warning(
            "Executing Human Handoff for conversation %s. Reason: %s",
            conversation_id,
            reason,
        )

        # 1. Label
        await self.add_labels(conversation_id, [settings.HANDOFF_LABEL])

        # 2. Status & Unassign
        await self.unassign_bot(conversation_id)
        await self.toggle_status(conversation_id, "open")

        # 3. Staff internal note
        note_content = (
            f"⚠️ [Automated Human Handoff Triggered]\n"
            f"Reason: {reason}\n"
            f"The AI assistant is now paused for this conversation so a human agent can assist."
        )
        await self.send_message(
            conversation_id, note_content, message_type="outgoing", private=True
        )

        # 4. Message to user
        notice = user_notice or settings.HANDOFF_USER_MESSAGE
        await self.send_message(
            conversation_id, notice, message_type="outgoing", private=False
        )

        return True


chatwoot_client = ChatwootClient()
