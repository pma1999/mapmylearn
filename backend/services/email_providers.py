"""
Email provider implementations.

Provides:
- EmailSendError: exception raised on unrecoverable send failure
- EmailProvider: base class interface
- SMTPEmailProvider: send via smtplib (STARTTLS or SSL)
- SendGridEmailProvider: send via SendGrid v3 API using requests
- get_email_provider: factory to obtain configured provider instance
"""
from __future__ import annotations

import os
import logging
import smtplib
from email.message import EmailMessage
from typing import Optional, Dict, Any

import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryError,
)

logger = logging.getLogger(__name__)


class EmailSendError(Exception):
    """Raised when an email cannot be sent by a provider."""


class EmailProvider:
    """Abstract email provider."""

    def send_email(self, to_email: str, subject: str, html_content: str, headers: Optional[Dict[str, str]] = None) -> None:
        """
        Send an email. Should raise EmailSendError on failure.

        :param to_email: recipient email
        :param subject: email subject
        :param html_content: html body
        :param headers: optional additional headers
        """
        raise NotImplementedError()


def _get_retry_decorator():
    """Create a tenacity retry decorator based on env settings."""
    max_attempts = int(os.getenv("EMAIL_RETRY_MAX_ATTEMPTS", "3"))
    base_backoff = float(os.getenv("EMAIL_RETRY_BACKOFF_SECONDS", "2"))

    return retry(
        reraise=True,
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=base_backoff, max=60),
        retry=retry_if_exception_type((EmailSendError, requests.RequestException, smtplib.SMTPException)),
    )


class SMTPEmailProvider(EmailProvider):
    """Email provider that sends over SMTP."""

    def __init__(self, host: str, port: int, username: Optional[str], password: Optional[str], use_tls: bool = True, timeout: int = 10, default_from: Optional[str] = None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.timeout = timeout
        self.default_from = default_from or os.getenv("DEFAULT_FROM_EMAIL", "no-reply@example.com")

    @_get_retry_decorator()
    def send_email(self, to_email: str, subject: str, html_content: str, headers: Optional[Dict[str, str]] = None) -> None:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.default_from
        msg["To"] = to_email
        if headers:
            for k, v in headers.items():
                msg[k] = v
        # Prefer HTML content; callers may include a plain-text fallback if desired.
        msg.set_content("This message contains HTML content. Enable an HTML-capable client to view it.")
        msg.add_alternative(html_content, subtype="html")

        try:
            # Use SMTP or SMTP_SSL depending on port and use_tls
            if self.use_tls and self.port in (587, 25):
                logger.debug("Connecting to SMTP (STARTTLS) %s:%s", self.host, self.port)
                server = smtplib.SMTP(self.host, self.port, timeout=self.timeout)
                server.ehlo()
                server.starttls()
                server.ehlo()
            elif not self.use_tls and self.port in (25, 1025, 587):
                logger.debug("Connecting to SMTP (no TLS) %s:%s", self.host, self.port)
                server = smtplib.SMTP(self.host, self.port, timeout=self.timeout)
            else:
                # For SMTPS explicit SSL (commonly 465)
                logger.debug("Connecting to SMTP SSL %s:%s", self.host, self.port)
                server = smtplib.SMTP_SSL(self.host, self.port, timeout=self.timeout)

            try:
                if self.username and self.password:
                    server.login(self.username, self.password)
                server.send_message(msg)
                logger.info("SMTP email sent to %s", to_email)
            finally:
                try:
                    server.quit()
                except Exception:
                    server.close()
        except Exception as exc:
            logger.exception("SMTP send failure for %s", to_email)
            # Wrap in EmailSendError to allow retry logic to trigger
            raise EmailSendError(str(exc)) from exc


class SendGridEmailProvider(EmailProvider):
    """SendGrid transactional provider using v3 mail/send endpoint."""

    SENDGRID_URL = "https://api.sendgrid.com/v3/mail/send"

    def __init__(self, api_key: str, timeout: int = 10, default_from: Optional[str] = None):
        if not api_key:
            raise ValueError("SendGrid API key must be provided")
        self.api_key = api_key
        self.timeout = timeout
        self.default_from = default_from or os.getenv("DEFAULT_FROM_EMAIL", "no-reply@example.com")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })

    @_get_retry_decorator()
    def send_email(self, to_email: str, subject: str, html_content: str, headers: Optional[Dict[str, str]] = None) -> None:
        payload: Dict[str, Any] = {
            "personalizations": [
                {
                    "to": [{"email": to_email}],
                    "subject": subject,
                }
            ],
            "from": {"email": self.default_from},
            "content": [{"type": "text/html", "value": html_content}],
        }
        if headers:
            # SendGrid supports custom headers under personalizations[0].headers
            payload["personalizations"][0]["headers"] = headers

        try:
            resp = self.session.post(self.SENDGRID_URL, json=payload, timeout=self.timeout)
            if resp.status_code >= 200 and resp.status_code < 300:
                logger.info("SendGrid email accepted for %s", to_email)
                return
            # For 4xx errors, don't retry except maybe 429. Wrap into EmailSendError
            logger.error("SendGrid returned %s: %s", resp.status_code, resp.text)
            raise EmailSendError(f"SendGrid error {resp.status_code}: {resp.text}")
        except requests.RequestException as exc:
            logger.exception("SendGrid request failed for %s", to_email)
            raise EmailSendError(str(exc)) from exc


def get_email_provider(provider_name: Optional[str] = None, override_kwargs: Optional[Dict[str, Any]] = None) -> EmailProvider:
    """
    Construct an EmailProvider based on environment variables or explicit provider_name.

    :param provider_name: 'sendgrid', 'smtp', or 'none'
    :param override_kwargs: provider-specific overrides (host, api_key, etc.)
    """
    provider = (provider_name or os.getenv("EMAIL_PROVIDER") or "sendgrid").lower()
    override_kwargs = override_kwargs or {}
    timeout = int(os.getenv("EMAIL_TIMEOUT_SECONDS", "10"))

    default_from = override_kwargs.get("default_from") or os.getenv("DEFAULT_FROM_EMAIL")

    if provider == "none":
        raise ValueError("EMAIL_PROVIDER set to 'none' - email disabled in this environment")

    if provider == "sendgrid":
        api_key = override_kwargs.get("sendgrid_api_key") or os.getenv("SENDGRID_API_KEY")
        if not api_key:
            raise ValueError("SENDGRID_API_KEY not configured for SendGrid provider")
        return SendGridEmailProvider(api_key=api_key, timeout=timeout, default_from=default_from)

    if provider == "smtp":
        host = override_kwargs.get("smtp_host") or os.getenv("SMTP_HOST")
        port = int(override_kwargs.get("smtp_port") or os.getenv("SMTP_PORT", 587))
        username = override_kwargs.get("smtp_username") or os.getenv("SMTP_USERNAME")
        password = override_kwargs.get("smtp_password") or os.getenv("SMTP_PASSWORD")
        use_tls_raw = override_kwargs.get("smtp_use_tls") or os.getenv("SMTP_USE_TLS", "true")
        use_tls = str(use_tls_raw).lower() in ("1", "true", "yes", "y")
        if not host:
            raise ValueError("SMTP_HOST not configured for SMTP provider")
        return SMTPEmailProvider(host=host, port=port, username=username, password=password, use_tls=use_tls, timeout=timeout, default_from=default_from)

    raise ValueError(f"Unknown EMAIL_PROVIDER: {provider}")
