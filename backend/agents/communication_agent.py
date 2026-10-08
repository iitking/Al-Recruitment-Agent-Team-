import uuid
from typing import Dict, Any, Optional
from backend.services.email_service import email_service

class CommunicationAgent:
    """
    Drafts approved candidate communications and dispatches them idempotently.
    """

    def draft_communication(
        self,
        candidate_name: str,
        recipient_email: str,
        job_title: str,
        template_type: str = "interview_invitation",
        extra_vars: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        rendered = email_service.render_template(
            template_type=template_type,
            candidate_name=candidate_name,
            job_title=job_title,
            extra_vars=extra_vars
        )

        idempotency_token = f"msg_{uuid.uuid4().hex[:12]}"

        return {
            "template_type": template_type,
            "recipient_email": recipient_email,
            "subject": rendered["subject"],
            "body": rendered["body"],
            "status": "draft",
            "idempotency_key": idempotency_token
        }

    def send_communication(
        self,
        recipient_email: str,
        subject: str,
        body: str,
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        return email_service.send_email(
            to_email=recipient_email,
            subject=subject,
            body=body,
            idempotency_key=idempotency_key
        )

communication_agent = CommunicationAgent()
