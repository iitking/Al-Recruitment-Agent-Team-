from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class CommunicationDraftRequest(BaseModel):
    template_type: str = Field(
        default="interview_invitation",
        description="interview_invitation, clarification, status_update, rejection"
    )
    custom_instructions: Optional[str] = None

class CommunicationSendRequest(BaseModel):
    subject: Optional[str] = None
    body: Optional[str] = None
    idempotency_key: Optional[str] = None

class CommunicationResponse(BaseModel):
    id: str
    candidate_id: str
    template_type: str
    recipient_email: str
    subject: str
    body: str
    status: str
    idempotency_key: Optional[str] = None
    sent_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
