import smtplib
import ssl
import os
import time
import socket
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Module logger
logger = logging.getLogger(__name__)

# Get SMTP settings from environment variables
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))  # Default to 587 (TLS)
SMTP_SSL_PORT = int(os.getenv("SMTP_SSL_PORT", 465))  # Default SSL port
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
MAIL_SENDER_EMAIL = os.getenv("MAIL_SENDER_EMAIL", "info@mapmylearn.com")

# Behavior controls
SMTP_TIMEOUT_SECONDS = int(os.getenv("SMTP_TIMEOUT", 30))
SMTP_RETRIES = int(os.getenv("SMTP_RETRIES", 3))
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
SMTP_USE_SSL = os.getenv("SMTP_USE_SSL", "true").lower() == "true"
SMTP_DEBUG = os.getenv("SMTP_DEBUG", "false").lower() == "true"
SMTP_FORCE_IPV4 = os.getenv("SMTP_FORCE_IPV4", "true").lower() == "true"

# Optionally force IPv4 resolution to avoid IPv6 egress issues on some hosts (e.g., PaaS)
if SMTP_FORCE_IPV4:
    _original_getaddrinfo = socket.getaddrinfo

    def _ipv4_only_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        try:
            results = _original_getaddrinfo(host, port, family, type, proto, flags)
        except Exception:
            return _original_getaddrinfo(host, port)
        ipv4_results = [r for r in results if r and r[0] == socket.AF_INET]
        return ipv4_results or results

    socket.getaddrinfo = _ipv4_only_getaddrinfo  # type: ignore
    logger.info("SMTP IPv4-only resolution enabled via SMTP_FORCE_IPV4=true")

def send_email(to_email: str, subject: str, html_content: str):
    """Sends an email using configured SMTP settings with retry and TLS/SSL fallback."""
    if not all([SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, MAIL_SENDER_EMAIL]):
        logger.error("SMTP settings not fully configured in environment variables. Cannot send email.")
        return False

    # Warn if sender address differs from authenticated user, which some providers reject
    try:
        if MAIL_SENDER_EMAIL and SMTP_USER and MAIL_SENDER_EMAIL.lower() != SMTP_USER.lower():
            logger.warning(
                "MAIL_SENDER_EMAIL (%s) differs from SMTP_USER (%s). Some providers (incl. IONOS) may reject or rewrite From.",
                MAIL_SENDER_EMAIL,
                SMTP_USER,
            )
    except Exception:
        # Do not fail sending due to logging issues
        pass

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = MAIL_SENDER_EMAIL
    message["To"] = to_email

    # Attach HTML content (could add a text alternative later)
    message.attach(MIMEText(html_content, "html"))

    def _log_dns_resolution():
        try:
            addrinfo = socket.getaddrinfo(SMTP_HOST, SMTP_PORT, 0, socket.SOCK_STREAM)
            resolved = []
            for family, socktype, proto, canonname, sockaddr in addrinfo:
                ip, _ = sockaddr
                resolved.append(f"{ip}({"IPv4" if family == socket.AF_INET else 'IPv6'})")
            if resolved:
                logger.info("SMTP host %s resolved to: %s", SMTP_HOST, ", ".join(resolved))
        except Exception as e:
            logger.warning("Could not resolve SMTP host %s: %s", SMTP_HOST, e)

    _log_dns_resolution()

    def _try_send_via_tls() -> bool:
        # Use a secure SSL context and prefer IPv4 by resolving first
        ssl_context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=SMTP_TIMEOUT_SECONDS) as server:
            if SMTP_DEBUG:
                server.set_debuglevel(1)
            server.ehlo()
            server.starttls(context=ssl_context)
            server.ehlo()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(MAIL_SENDER_EMAIL, to_email, message.as_string())
            return True

    def _try_send_via_ssl() -> bool:
        ssl_context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_SSL_PORT, context=ssl_context, timeout=SMTP_TIMEOUT_SECONDS) as server:
            if SMTP_DEBUG:
                server.set_debuglevel(1)
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(MAIL_SENDER_EMAIL, to_email, message.as_string())
            return True

    for attempt_number in range(1, SMTP_RETRIES + 1):
        # Try TLS first if enabled
        if SMTP_USE_TLS:
            try:
                if _try_send_via_tls():
                    logger.info(f"Email sent successfully to {to_email} via TLS ({SMTP_HOST}:{SMTP_PORT}) on attempt {attempt_number}")
                    return True
            except smtplib.SMTPAuthenticationError:
                logger.error(f"SMTP authentication failed for user '{SMTP_USER}'. Check credentials.")
                return False
            except (smtplib.SMTPServerDisconnected, smtplib.SMTPConnectError, socket.timeout, OSError, TimeoutError) as e:
                logger.warning(
                    f"Attempt {attempt_number}: TLS send failed to {to_email} via {SMTP_HOST}:{SMTP_PORT} — {type(e).__name__}: {e}"
                )
            except Exception as e:
                logger.error(f"Attempt {attempt_number}: Unexpected TLS error sending to {to_email}: {e}")

        # Fallback to SSL if enabled
        if SMTP_USE_SSL:
            try:
                if _try_send_via_ssl():
                    logger.info(f"Email sent successfully to {to_email} via SSL ({SMTP_HOST}:{SMTP_SSL_PORT}) on attempt {attempt_number}")
                    return True
            except smtplib.SMTPAuthenticationError:
                logger.error(f"SMTP authentication failed for user '{SMTP_USER}' (SSL). Check credentials.")
                return False
            except (smtplib.SMTPServerDisconnected, smtplib.SMTPConnectError, socket.timeout, OSError, TimeoutError) as e:
                logger.warning(
                    f"Attempt {attempt_number}: SSL send failed to {to_email} via {SMTP_HOST}:{SMTP_SSL_PORT} — {type(e).__name__}: {e}"
                )
            except Exception as e:
                logger.error(f"Attempt {attempt_number}: Unexpected SSL error sending to {to_email}: {e}")

        # Backoff before next attempt if there will be one
        if attempt_number < SMTP_RETRIES:
            sleep_seconds = min(2 ** (attempt_number - 1), 10)
            time.sleep(sleep_seconds)

    logger.error(
        f"Failed to send email to {to_email} after {SMTP_RETRIES} attempts. "
        f"Tried TLS({SMTP_USE_TLS}) on {SMTP_HOST}:{SMTP_PORT} and SSL({SMTP_USE_SSL}) on {SMTP_HOST}:{SMTP_SSL_PORT}."
    )
    return False

def send_verification_email(to_email: str, verification_link: str):
    """Sends the email verification email."""
    subject = "Verify Your Email Address for MapMyLearn"
    
    # Simple HTML email template
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
    
    return send_email(to_email, subject, html_content)

def send_password_reset_email(to_email: str, reset_link: str):
    """Sends the password reset email."""
    subject = "Reset Your MapMyLearn Password"
    # Simple HTML email template for password reset
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
    return send_email(to_email, subject, html_content)

def send_password_reset_confirmation_email(to_email: str):
    """Sends an email confirming the password has been reset."""
    subject = "Your MapMyLearn Password Has Been Changed"
    # Simple HTML email template for confirmation
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
    return send_email(to_email, subject, html_content) 