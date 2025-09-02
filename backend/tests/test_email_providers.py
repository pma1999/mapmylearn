import os
import smtplib
import pytest
import requests

from backend.services.email_providers import (
    get_email_provider,
    SendGridEmailProvider,
    SMTPEmailProvider,
    EmailSendError,
)


def test_get_email_provider_sendgrid_missing_api_key(monkeypatch):
    monkeypatch.setenv("EMAIL_PROVIDER", "sendgrid")
    monkeypatch.delenv("SENDGRID_API_KEY", raising=False)
    with pytest.raises(ValueError):
        get_email_provider()


def test_get_email_provider_smtp_missing_host(monkeypatch):
    monkeypatch.setenv("EMAIL_PROVIDER", "smtp")
    monkeypatch.delenv("SMTP_HOST", raising=False)
    with pytest.raises(ValueError):
        get_email_provider()


def test_sendgrid_send_email_accepted(monkeypatch):
    # Arrange
    provider = SendGridEmailProvider(api_key="dummy-key", timeout=1, default_from="no-reply@example.com")

    class DummyResp:
        status_code = 202
        text = "accepted"

    def fake_post(self, url, json, timeout):
        return DummyResp()

    monkeypatch.setattr(requests.Session, "post", fake_post)

    # Act / Assert -- should not raise
    provider.send_email("user@example.com", "subj", "<p>html</p>")


def test_sendgrid_send_email_client_error_raises(monkeypatch):
    provider = SendGridEmailProvider(api_key="dummy-key", timeout=1, default_from="no-reply@example.com")

    class DummyResp:
        status_code = 400
        text = "bad request"

    def fake_post(self, url, json, timeout):
        return DummyResp()

    monkeypatch.setattr(requests.Session, "post", fake_post)

    with pytest.raises(EmailSendError):
        provider.send_email("user@example.com", "subj", "<p>html</p>")


def test_smtp_provider_connection_failure_raises(monkeypatch):
    # Create provider with bogus host/port
    provider = SMTPEmailProvider(host="invalid-host", port=25, username=None, password=None, use_tls=False, timeout=1)

    class FakeSMTP:
        def __init__(self, *args, **kwargs):
            raise smtplib.SMTPConnectError(421, "Cannot connect")

    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)
    monkeypatch.setattr(smtplib, "SMTP_SSL", FakeSMTP)

    with pytest.raises(EmailSendError):
        provider.send_email("user@example.com", "subj", "<p>html</p>")
