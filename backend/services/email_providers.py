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
    """Create a tenacity retry decorator based on env settings.

    Defaults have been increased to be more tolerant of intermittent network issues:
    - Default max attempts: 5 (was 3)
    - Default base backoff multiplier: 4s (was 2s)
    - Default max wait cap: 120s (was 60s)
    These can still be tuned via environment variables.
    """
    max_attempts = int(os.getenv("EMAIL_RETRY_MAX_ATTEMPTS", "5"))
    base_backoff = float(os.getenv("EMAIL_RETRY_BACKOFF_SECONDS", "4"))

    return retry(
        reraise=True,
        stop=stop_after_attempt(max_attempts),
        # larger max and multiplier to tolerate transient network blips
        wait=wait_exponential(multiplier=base_backoff, max=120),
        retry=retry_if_exception_type((EmailSendError, requests.RequestException, smtplib.SMTPException)),
    )


class SMTPEmailProvider(EmailProvider):
    """Email provider that sends over SMTP."""

    def __init__(self, host: str, port: int, username: Optional[str], password: Optional[str], use_tls: bool = True, timeout: int = 30, default_from: Optional[str] = None):
        """
        Increased default timeout (30s) to reduce false timeouts caused by transient network issues.
        Note: the factory get_email_provider still passes EMAIL_TIMEOUT_SECONDS when present.
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.timeout = timeout
        self.default_from = default_from or os.getenv("DEFAULT_FROM_EMAIL", "no-reply@example.com")

    @_get_retry_decorator()
    def send_email(self, to_email: str, subject: str, html_content: str, headers: Optional[Dict[str, str]] = None) -> None:
        # Local imports so file-level imports remain minimal and safe for test envs
        import socket
        import time
        import traceback

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

        # Mask username for logs to avoid leaking secrets
        masked_user = None
        if self.username:
            try:
                if "@" in self.username:
                    local, domain = self.username.split("@", 1)
                    masked_user = f"{local[:1]}***@{domain}"
                else:
                    masked_user = f"{self.username[:1]}***"
            except Exception:
                masked_user = "***"

        logger.debug(
            "SMTP send attempt: to=%s host=%s port=%s timeout=%s user=%s provider_use_tls=%s",
            to_email,
            self.host,
            self.port,
            self.timeout,
            masked_user,
            self.use_tls,
        )

        start_ts = time.time()
        server = None
        try:
            # Before attempting smtplib connection, resolve the host and probe addresses.
            # This gives actionable logs for intermittent DNS/routing issues.
            try:
                addrs = []
                for af, socktype, proto, canonname, sa in socket.getaddrinfo(self.host, self.port, 0, socket.SOCK_STREAM):
                    addrs.append(sa)
                logger.debug("Resolved SMTP host %s to addresses: %s", self.host, addrs)
            except Exception as exc:
                logger.warning("Failed to resolve SMTP host %s: %s", self.host, exc)
                addrs = []

            # Try to connect to each resolved IP with a short probe to detect network reachability
            probe_timeout = min(5, max(2, int(self.timeout / 2)))
            probe_success = False
            probe_errors = []
            if addrs:
                for sa in addrs:
                    try:
                        logger.debug("Probing SMTP address %s (timeout=%s)", sa, probe_timeout)
                        sock = socket.create_connection(sa, probe_timeout)
                        sock.close()
                        probe_success = True
                        logger.debug("Probe succeeded for %s", sa)
                        break
                    except Exception as pexc:
                        probe_errors.append((sa, str(pexc)))
                        logger.debug("Probe failed for %s: %s", sa, pexc)
            else:
                # If resolution failed or returned nothing, still attempt connection via hostname (may succeed via alternate DNS)
                logger.debug("No resolved addresses to probe; will attempt direct smtplib connect to host")

            # Use SMTP or SMTP_SSL depending on port and use_tls
            if self.use_tls and self.port in (587, 25):
                logger.debug("Connecting to SMTP (STARTTLS) %s:%s", self.host, self.port)
                try:
                    server = smtplib.SMTP(self.host, self.port, timeout=self.timeout)
                except Exception as exc:
                    logger.exception("Failed to establish SMTP connection (STARTTLS) to %s:%s", self.host, self.port)
                    # Add probe info into the error message for debugging
                    probe_info = "; ".join([f"{sa}:{err}" for sa, err in probe_errors]) if probe_errors else "no-probe-info"
                    raise EmailSendError(f"Connection failed: {exc} (probe:{probe_info})") from exc
                try:
                    server.ehlo()
                    server.starttls()
                    server.ehlo()
                except Exception as exc:
                    logger.exception("STARTTLS negotiation failed with %s:%s", self.host, self.port)
                    raise EmailSendError(f"STARTTLS negotiation failed: {exc}") from exc
            elif not self.use_tls and self.port in (25, 1025, 587):
                logger.debug("Connecting to SMTP (no TLS) %s:%s", self.host, self.port)
                try:
                    server = smtplib.SMTP(self.host, self.port, timeout=self.timeout)
                except Exception as exc:
                    logger.exception("Failed to establish plain SMTP connection to %s:%s", self.host, self.port)
                    probe_info = "; ".join([f"{sa}:{err}" for sa, err in probe_errors]) if probe_errors else "no-probe-info"
                    raise EmailSendError(f"Connection failed: {exc} (probe:{probe_info})") from exc
            else:
                # For SMTPS explicit SSL (commonly 465)
                logger.debug("Connecting to SMTP SSL %s:%s", self.host, self.port)
                try:
                    server = smtplib.SMTP_SSL(self.host, self.port, timeout=self.timeout)
                except Exception as exc:
                    logger.exception("Failed to establish SMTPS (SSL) connection to %s:%s", self.host, self.port)
                    probe_info = "; ".join([f"{sa}:{err}" for sa, err in probe_errors]) if probe_errors else "no-probe-info"
                    raise EmailSendError(f"Connection failed: {exc} (probe:{probe_info})") from exc

            # At this point server is connected (or exception raised)
            try:
                if self.username and self.password:
                    logger.debug("Attempting SMTP login for user=%s", masked_user)
                    try:
                        server.login(self.username, self.password)
                        logger.debug("SMTP login successful for user=%s", masked_user)
                    except smtplib.SMTPAuthenticationError as auth_exc:
                        logger.error("SMTP authentication failed for user=%s: %s", masked_user, auth_exc)
                        raise EmailSendError(f"Authentication failed: {auth_exc}") from auth_exc
                    except Exception as exc:
                        logger.exception("Unexpected error during SMTP login for user=%s", masked_user)
                        raise EmailSendError(f"Login error: {exc}") from exc

                # Send the message and capture any low-level socket errors separately
                try:
                    server.send_message(msg)
                    elapsed = time.time() - start_ts
                    logger.info("SMTP email sent to %s (elapsed=%.2fs)", to_email, elapsed)
                except (smtplib.SMTPException, socket.timeout, OSError) as send_exc:
                    logger.exception("Failed to send message to %s via %s:%s", to_email, self.host, self.port)
                    raise EmailSendError(f"Send failed: {send_exc}") from send_exc
            finally:
                # Best-effort server shutdown
                try:
                    server.quit()
                except Exception as close_exc:
                    logger.debug("Failed to quit SMTP server cleanly: %s", close_exc)
                    try:
                        server.close()
                    except Exception:
                        logger.debug("Failed to close SMTP connection cleanly")
        except EmailSendError:
            # Re-raise EmailSendError as-is so tenacity can handle retries
            raise
        except Exception as exc:
            # Log full traceback for investigation and wrap in EmailSendError
            logger.error("SMTP send failure for %s\nException: %s\nTraceback:\n%s", to_email, exc, traceback.format_exc())
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
