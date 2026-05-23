import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In development (MAIL_USERNAME is blank), emails are NOT sent.
# The token/link is logged to the console so you can test manually.
# In production, set MAIL_USERNAME/PASSWORD to your SMTP provider credentials.
# ---------------------------------------------------------------------------

def _is_email_configured() -> bool:
    return bool(settings.MAIL_USERNAME and settings.MAIL_PASSWORD)


def _log_dev_email(subject: str, to: str, body: str) -> None:
    logger.info("━━━ DEV EMAIL (not sent) ━━━")
    logger.info("To:      %s", to)
    logger.info("Subject: %s", subject)
    logger.info("Body:\n%s", body)
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━")


async def send_password_reset_email(to_email: str, plain_token: str) -> None:
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={plain_token}"
    subject = "Reset your SPTS password"
    body = (
        f"You requested a password reset.\n\n"
        f"Click the link below to set a new password (expires in 1 hour):\n\n"
        f"{reset_url}\n\n"
        f"If you did not request this, ignore this email."
    )

    if not _is_email_configured():
        _log_dev_email(subject, to_email, body)
        return

    try:
        from fastapi_mail import FastMail, MessageSchema, MessageType, ConnectionConfig
        conf = ConnectionConfig(
            MAIL_USERNAME=settings.MAIL_USERNAME,
            MAIL_PASSWORD=settings.MAIL_PASSWORD,
            MAIL_FROM=settings.MAIL_FROM,
            MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
            MAIL_PORT=settings.MAIL_PORT,
            MAIL_SERVER=settings.MAIL_SERVER,
            MAIL_STARTTLS=True,
            MAIL_SSL_TLS=False,
        )
        message = MessageSchema(subject=subject, recipients=[to_email], body=body, subtype=MessageType.plain)
        await FastMail(conf).send_message(message)
        logger.info("Password reset email sent to %s", to_email)
    except Exception:
        logger.exception("Failed to send password reset email to %s", to_email)


async def send_subscription_expiry_reminder(to_email: str, school_name: str, days_remaining: int) -> None:
    subject = f"SPTS: Subscription expiring in {days_remaining} day(s)"
    body = (
        f"Dear {school_name},\n\n"
        f"Your SPTS subscription expires in {days_remaining} day(s).\n\n"
        f"After expiry you will have a 7-day grace period before write access is locked.\n\n"
        f"Please contact support to renew.\n\n"
        f"— SPTS Team"
    )

    if not _is_email_configured():
        _log_dev_email(subject, to_email, body)
        return

    try:
        from fastapi_mail import FastMail, MessageSchema, MessageType, ConnectionConfig
        conf = ConnectionConfig(
            MAIL_USERNAME=settings.MAIL_USERNAME,
            MAIL_PASSWORD=settings.MAIL_PASSWORD,
            MAIL_FROM=settings.MAIL_FROM,
            MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
            MAIL_PORT=settings.MAIL_PORT,
            MAIL_SERVER=settings.MAIL_SERVER,
            MAIL_STARTTLS=True,
            MAIL_SSL_TLS=False,
        )
        message = MessageSchema(subject=subject, recipients=[to_email], body=body, subtype=MessageType.plain)
        await FastMail(conf).send_message(message)
    except Exception:
        logger.exception("Failed to send subscription reminder to %s", to_email)
