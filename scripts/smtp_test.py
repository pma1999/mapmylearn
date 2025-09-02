import smtplib
import traceback
from email.message import EmailMessage
import os

host = os.getenv("SMTP_HOST", "smtp.ionos.es")
port = int(os.getenv("SMTP_PORT", "587"))
user = os.getenv("SMTP_USERNAME", "info@mapmylearn.com")
password = os.getenv("SMTP_PASSWORD", "z8JPgXNk3f@mTaH")
to = os.getenv("SMTP_TEST_TO", "lahegemoniapodcast@gmail.com")

msg = EmailMessage()
msg["Subject"] = "MapMyLearn SMTP test"
msg["From"] = user
msg["To"] = to
msg.set_content("Plain text fallback for SMTP test")
msg.add_alternative("<html><body><p>MapMyLearn SMTP test</p></body></html>", subtype="html")

print(f"Testing SMTP connect to {host}:{port} as {user} -> {to}")
try:
    s = smtplib.SMTP(host, port, timeout=30)
    s.ehlo()
    # Attempt STARTTLS if using 587
    try:
        s.starttls()
        s.ehlo()
        print("STARTTLS negotiated")
    except Exception as e:
        print("STARTTLS not used / failed: ", e)
    try:
        s.login(user, password)
        print("Login succeeded")
    except Exception as e:
        print("Login failed:", e)
    try:
        s.send_message(msg)
        print("SENT")
    except Exception as e:
        print("Send failed:", e)
    try:
        s.quit()
    except Exception:
        pass
except Exception:
    traceback.print_exc()
    print("ERROR: sending failed")
