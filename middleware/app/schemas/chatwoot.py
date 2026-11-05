from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Sender(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    type: Optional[str] = None  # "contact" or "user"
    email: Optional[str] = None


class Conversation(BaseModel):
    id: int
    status: Optional[str] = "open"  # "open", "resolved", "pending"
    channel: Optional[str] = None
    labels: Optional[List[str]] = []
    assignee_id: Optional[int] = None
    team_id: Optional[int] = None
    custom_attributes: Optional[Dict[str, Any]] = {}


class Account(BaseModel):
    id: int
    name: Optional[str] = None


class ChatwootWebhookPayload(BaseModel):
    event: str
    id: Optional[int] = None
    content: Optional[str] = None
    content_type: Optional[str] = "text"
    message_type: Optional[str] = None  # "incoming", "outgoing"
    private: Optional[bool] = False
    sender: Optional[Sender] = None
    conversation: Optional[Conversation] = None
    account: Optional[Account] = None
