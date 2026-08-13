# from app.core.email import send_email

# @shared_task
# def send_otp_email_task(email: str, otp: str):
#     """Send OTP email asynchronously."""
#     subject = "Your OTP for eBazar"
#     body = f"Your OTP is: {otp}. It expires in 5 minutes."
#     send_email(email, subject, body)

# @shared_task
# def send_welcome_email_task(email: str, full_name: str):
#     """Send welcome email after registration."""
#     subject = "Welcome to eBazar!"
#     body = f"Hi {full_name},\n\nWelcome to eBazar! Your account has been successfully created.\n\nBest regards,\neBazar Team"
#     send_email(email, subject, body)