import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, Any, Optional
from backend.core.config import settings

class EmailService:
    def __init__(self):
        self.sent_outbox: list = []  # In-memory record for testing & observability

    def render_template(
        self,
        template_type: str,
        candidate_name: str,
        job_title: str,
        extra_vars: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        extra = extra_vars or {}
        name = candidate_name or "Candidate"

        if template_type == "interview_invitation":
            subject = f"Interview Invitation: {job_title} at Our Team"
            slots_text = extra.get("slots_text", "We would like to coordinate a 45-minute technical conversation.")
            meeting_link = extra.get("meeting_link", "")
            body = (
                f"Dear {name},\n\n"
                f"Thank you for applying for the {job_title} position. Based on your qualifications, we are pleased to invite you to an interview.\n\n"
                f"{slots_text}\n"
                f"{f'Meeting Link: {meeting_link}' if meeting_link else ''}\n\n"
                f"Please let us know your preferred availability or confirm the proposed time.\n\n"
                f"Best regards,\nRecruitment Team"
            )

        elif template_type == "clarification":
            missing_items = extra.get("missing_items", "additional details regarding your recent project experience")
            subject = f"Follow-up regarding your application for {job_title}"
            body = (
                f"Dear {name},\n\n"
                f"Thank you for your interest in the {job_title} role. We are currently reviewing your application.\n\n"
                f"Could you please provide some brief clarification on the following:\n- {missing_items}\n\n"
                f"Looking forward to hearing from you.\n\n"
                f"Best regards,\nRecruitment Team"
            )

        elif template_type == "rejection":
            subject = f"Update regarding your application for {job_title}"
            body = (
                f"Dear {name},\n\n"
                f"Thank you for taking the time to apply for the {job_title} role. While we were impressed with your background, we have decided to move forward with other candidates whose experience aligns more closely with our current requirements.\n\n"
                f"We appreciate your interest and wish you the best in your job search.\n\n"
                f"Sincerely,\nRecruitment Team"
            )

        else:
            subject = f"Status Update on your application for {job_title}"
            notes = extra.get("notes", "Your application is currently under review.")
            body = (
                f"Dear {name},\n\n"
                f"Here is a status update regarding your application for {job_title}:\n\n"
                f"{notes}\n\n"
                f"Best regards,\nRecruitment Team"
            )

        return {"subject": subject, "body": body}

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sends email via SMTP if configured; otherwise records into outbox log (mock mode).
        """
        # Idempotency check against outbox
        if idempotency_key:
            for item in self.sent_outbox:
                if item.get("idempotency_key") == idempotency_key:
                    return {
                        "status": "already_sent",
                        "message": "Email previously sent under this idempotency key",
                        "idempotency_key": idempotency_key,
                        "timestamp": item.get("timestamp")
                    }

        timestamp = datetime.utcnow().isoformat()
        log_entry = {
            "to": to_email,
            "subject": subject,
            "body": body,
            "idempotency_key": idempotency_key,
            "timestamp": timestamp,
            "delivered_via": "smtp" if settings.SMTP_HOST else "mock_outbox"
        }

        # Real SMTP attempt if host configured
        if settings.SMTP_HOST and settings.SMTP_USER:
            try:
                msg = MIMEMultipart()
                msg["From"] = settings.FROM_EMAIL
                msg["To"] = to_email
                msg["Subject"] = subject
                msg.attach(MIMEText(body, "plain"))

                with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                    server.starttls()
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.send_message(msg)
                log_entry["smtp_status"] = "success"
            except Exception as e:
                log_entry["smtp_status"] = f"failed: {str(e)}"

        self.sent_outbox.append(log_entry)
        return {
            "status": "sent",
            "delivered_via": log_entry["delivered_via"],
            "timestamp": timestamp,
            "idempotency_key": idempotency_key
        }

email_service = EmailService()
