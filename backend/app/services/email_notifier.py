"""
Email notification service for new user suggestions, feedback, and waitlist signups.
Sends email alerts to the founder inbox via SMTP (e.g. Gmail / SendGrid / Resend).
Non-blocking: executed in FastAPI BackgroundTasks without slowing down user responses.
"""
from __future__ import annotations

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional
from dotenv import load_dotenv

logger = logging.getLogger("email_notifier")


def send_suggestion_alert(
    *,
    suggestion_id: str,
    text: str,
    category: str,
    submitter_email: Optional[str] = None,
    created_at: Optional[str] = None,
) -> bool:
    """
    Send an email alert to the founder when a user submits a suggestion or feedback.
    Reads SMTP configuration from environment variables.
    """
    load_dotenv()
    admin_recipient = os.getenv("ADMIN_NOTIFICATION_EMAIL", "deveshsingh20666@gmail.com").strip().strip('"').strip("'")
    smtp_host = os.getenv("SMTP_HOST", "").strip().strip('"').strip("'")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "").strip().strip('"').strip("'")
    smtp_password = os.getenv("SMTP_PASSWORD", "").strip()
    if (smtp_password.startswith('"') and smtp_password.endswith('"')) or (smtp_password.startswith("'") and smtp_password.endswith("'")):
        smtp_password = smtp_password[1:-1].strip()
    smtp_from = os.getenv("SMTP_FROM", smtp_user or "noreply@resumeroast.app").strip().strip('"').strip("'")

    if not (smtp_host and smtp_user and smtp_password):
        logger.info(
            f"[EMAIL_ALERT_SKIPPED] Suggestion #{suggestion_id} saved in database & visible on /stats. "
            "To receive instant Gmail/email alerts, set SMTP_HOST, SMTP_USER, and SMTP_PASSWORD in backend/.env."
        )
        return False

    try:
        subject = f"💡 New Resume Roast Suggestion [{category.upper()}]"
        
        contact_line = (
            f"User Email: {submitter_email} (Reply directly to reach them)"
            if submitter_email
            else "User Email: Anonymous (No email provided)"
        )

        plain_text = f"""
New Suggestion Received on Resume Roast!
========================================

Category: {category.upper()}
Timestamp: {created_at or 'Just now'}
{contact_line}

Suggestion Content:
-------------------
"{text}"

Suggestion ID: {suggestion_id}
View all submissions in your Admin Dashboard:
https://resumeroast.app/stats
"""

        html_body = f"""<!DOCTYPE html>
<html>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #120F0D; color: #F5EFE0; padding: 24px;">
    <div style="max-width: 580px; margin: 0 auto; background-color: #1A1613; border: 1px solid rgba(255,255,255,0.12); border-radius: 8px; padding: 24px;">
        <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 12px; margin-bottom: 18px;">
            <span style="font-size: 11px; font-weight: bold; letter-spacing: 0.05em; color: #FFB93C; text-transform: uppercase;">
                💡 FOUNDER SUGGESTION ALERT
            </span>
            <span style="font-size: 11px; background-color: rgba(232,66,45,0.2); color: #E8422D; border: 1px solid rgba(232,66,45,0.3); padding: 2px 8px; border-radius: 4px; font-weight: bold; text-transform: uppercase;">
                {category}
            </span>
        </div>

        <h2 style="color: #FFFFFF; font-size: 20px; margin-top: 0; margin-bottom: 14px;">
            A user just left an idea on your desk:
        </h2>

        <div style="background-color: rgba(0,0,0,0.4); border-left: 3px solid #FFB93C; border-radius: 4px; padding: 14px; margin-bottom: 20px; font-size: 14px; line-height: 1.6; color: #F5EFE0; white-space: pre-wrap;">
{text}
        </div>

        <table style="width: 100%; font-size: 12px; color: #8A8168; border-collapse: collapse; margin-bottom: 24px;">
            <tr>
                <td style="padding: 4px 0;"><strong>Submitter:</strong></td>
                <td style="padding: 4px 0; color: #FFB93C;">{submitter_email or 'Anonymous'}</td>
            </tr>
            <tr>
                <td style="padding: 4px 0;"><strong>Timestamp:</strong></td>
                <td style="padding: 4px 0; color: #C9BFA6;">{created_at or 'Just now'} UTC</td>
            </tr>
            <tr>
                <td style="padding: 4px 0;"><strong>ID:</strong></td>
                <td style="padding: 4px 0; font-family: monospace; color: #8A8168;">{suggestion_id}</td>
            </tr>
        </table>

        <div style="text-align: center; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.08);">
            <a href="https://resumeroast.app/stats" style="display: inline-block; background-color: #E8422D; color: #FFFFFF; text-decoration: none; font-size: 12px; font-weight: bold; padding: 10px 20px; border-radius: 4px;">
                Open Founder Dashboard (/stats) →
            </a>
        </div>
    </div>
</body>
</html>"""

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = smtp_from
        msg["To"] = admin_recipient
        if submitter_email:
            msg["Reply-To"] = submitter_email

        msg.attach(MIMEText(plain_text, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_from, [admin_recipient], msg.as_string())

        logger.info(f"[EMAIL_SENT] Suggestion alert #{suggestion_id} sent to {admin_recipient}")
        return True
    except Exception as exc:
        logger.error(f"[EMAIL_FAILED] Could not send suggestion email: {exc}")
        return False
