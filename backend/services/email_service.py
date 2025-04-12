import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get SMTP settings from environment variables
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587)) # Default to 587 (TLS)
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
MAIL_SENDER_EMAIL = os.getenv("MAIL_SENDER_EMAIL", "info@mapmylearn.com")

def send_email(to_email: str, subject: str, html_content: str):
    """Sends an email using configured SMTP settings."""
    if not all([SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, MAIL_SENDER_EMAIL]):
        print("ERROR: SMTP settings not fully configured in environment variables. Cannot send email.")
        # In a real app, you might raise an exception or handle this more gracefully
        return False

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = MAIL_SENDER_EMAIL
    message["To"] = to_email

    # Attach HTML content
    # It's good practice to also include a plain text version, but keeping it simple for now
    message.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo() # Can be omitted
            server.starttls() # Secure the connection
            server.ehlo() # Can be omitted
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(MAIL_SENDER_EMAIL, to_email, message.as_string())
            print(f"Email sent successfully to {to_email}")
            return True
    except smtplib.SMTPAuthenticationError:
        print(f"ERROR: SMTP Authentication failed for user {SMTP_USER}. Check credentials.")
        return False
    except Exception as e:
        print(f"ERROR: Failed to send email to {to_email}: {e}")
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