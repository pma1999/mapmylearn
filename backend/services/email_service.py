"""
Central email service coordinator.

Replaces the previous SMTP-only helper with a provider-agnostic coordinator that:
- Uses backend.services.email_providers.get_email_provider to obtain a provider
- Relies on provider implementations to perform retries/timeouts
- Raises EmailSendError on unrecoverable failure so callers (routes) can make transaction decisions

Note: callers should expect EmailSendError on failure. This file keeps the previous helper function names
(send_email, send_verification_email, send_password_reset_email, send_password_reset_confirmation_email)
but now raises on failure instead of returning False.
"""
from __future__ import annotations

import os
import logging
from dotenv import load_dotenv

from backend.services.email_providers import get_email_provider, EmailSendError

load_dotenv()
logger = logging.getLogger(__name__)


def _get_provider():
    # Lazily instantiate provider from environment. Tests can call get_email_provider directly if needed.
    return get_email_provider()


def send_email(to_email: str, subject: str, html_content: str, headers: dict | None = None) -> None:
    """
    Send an email using configured provider.

    Raises:
        EmailSendError: when sending fails after provider retries.
    """
    provider = _get_provider()
    try:
        provider.send_email(to_email=to_email, subject=subject, html_content=html_content, headers=headers)
        logger.info("Email successfully sent to %s via provider", to_email)
    except EmailSendError:
        # Re-raise to allow upstream logic (e.g., registration flow) to rollback transactions.
        logger.exception("EmailSendError while sending email to %s", to_email)
        raise
    except Exception as exc:
        # Wrap unexpected exceptions to EmailSendError so callers get a consistent exception type.
        logger.exception("Unexpected error while sending email to %s: %s", to_email, exc)
        raise EmailSendError(str(exc)) from exc


def send_verification_email(to_email: str, verification_link: str) -> None:
    """Sends the email verification email. Raises EmailSendError on failure."""
    subject = "Verify Your Email Address for MapMyLearn"
    html_content = f"""
    <html>
    <head></head>
    <body>
        <h2>Welcome to MapMyLearn!</h2>
        <p>Thank you for registering. Please click the link below to verify your email address:</p>
        <p><a href="{verification_link}">Verify Email Address</a></p>
        <p>This link will expire in 1 hour.</p>
        <p>If you did not register for an account, please ignore this email.</p>
        <br>
        <p>Thanks,</p>
        <p>The MapMyLearn Team</p>
    </body>
    </html>
    """
    send_email(to_email=to_email, subject=subject, html_content=html_content)


def send_password_reset_email(to_email: str, reset_link: str) -> None:
    """Sends the password reset email. Raises EmailSendError on failure."""
    subject = "Reset Your MapMyLearn Password"
    html_content = f"""
    <html>
    <head></head>
    <body>
        <h2>Reset Your MapMyLearn Password</h2>
        <p>We received a request to reset the password for your account associated with this email address.</p>
        <p>Click the link below to set a new password:</p>
        <p><a href="{reset_link}">Reset Password</a></p>
        <p>This link will expire in 30 minutes.</p>
        <p>If you did not request a password reset, please ignore this email or contact support if you have concerns.</p>
        <br>
        <p>Thanks,</p>
        <p>The MapMyLearn Team</p>
    </body>
    </html>
    """
    send_email(to_email=to_email, subject=subject, html_content=html_content)


def send_password_reset_confirmation_email(to_email: str) -> None:
    """Sends an email confirming the password has been reset. Raises EmailSendError on failure."""
    subject = "Your MapMyLearn Password Has Been Changed"
    html_content = f"""
    <html>
    <head></head>
    <body>
        <h2>Password Changed Successfully</h2>
        <p>The password for your MapMyLearn account associated with this email address has been successfully changed.</p>
        <p>If you did not make this change, please contact our support team immediately.</p>
        <br>
        <p>Thanks,</p>
        <p>The MapMyLearn Team</p>
    </body>
    </html>
    """
    send_email(to_email=to_email, subject=subject, html_content=html_content)
