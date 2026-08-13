import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from app.core.config import settings


class EmailService:
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT or 587
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD.get_secret_value() if settings.SMTP_PASSWORD else None
        self.from_email = settings.SMTP_USER or "noreply@ebazar.com"

    def send_email(self, to_email: str, subject: str, body: str, html: Optional[str] = None) -> bool:
        """Send an email using SMTP."""
        if not self.smtp_host or not self.smtp_user or not self.smtp_password:
            print(f"Email not configured. Would send to {to_email}: {subject}")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = to_email

            part1 = MIMEText(body, "plain")
            msg.attach(part1)

            if html:
                part2 = MIMEText(html, "html")
                msg.attach(part2)

            with smtplib.SMTP(self.smtp_host, int(self.smtp_port)) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_email, to_email, msg.as_string())

            return True
        except Exception as e:
            print(f"Failed to send email to {to_email}: {e}")
            return False

    def send_otp_email(self, email: str, otp: str) -> bool:
        """Send OTP via email."""
        subject = "Your OTP for eBazar Registration"
        body = f"""
Your OTP for eBazar registration is: {otp}

This OTP is valid for 5 minutes.

If you did not request this, please ignore this email.

Best regards,
eBazar Team
"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
        .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .otp {{ font-size: 32px; font-weight: bold; color: #4CAF50; text-align: center; padding: 20px; letter-spacing: 5px; }}
        .footer {{ margin-top: 30px; text-align: center; color: #888; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <h2 style="text-align: center; color: #333;">eBazar OTP Verification</h2>
        <p>Your OTP for registration is:</p>
        <div class="otp">{otp}</div>
        <p>This OTP is valid for <strong>5 minutes</strong>.</p>
        <p>If you did not request this, please ignore this email.</p>
        <div class="footer">
            <p>&copy; 2026 eBazar. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""
        return self.send_email(email, subject, body, html)


# Singleton instance
email_service = EmailService()

# Convenience function for Celery tasks
def send_email(to_email: str, subject: str, body: str, html: Optional[str] = None) -> bool:
    """Convenience function to send email using the singleton service."""
    return email_service.send_email(to_email, subject, body, html)

def send_otp_email(email: str, otp: str) -> bool:
    """Convenience function to send OTP email."""
    return email_service.send_otp_email(email, otp)