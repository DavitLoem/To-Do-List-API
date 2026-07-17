import os
import aiosmtplib
from email.message import EmailMessage
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader

load_dotenv()

BREVO_SMTP_KEY = os.getenv("BREVO_API_KEY")
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
MAIL_FROM_ADDRESS = os.getenv("MAIL_FROM_ADDRESS")
MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME", "To Do List")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "templates", "email")
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))


async def send_otp_email(recipient_email: str, otp_code: str):
    if not BREVO_SMTP_KEY or not SMTP_USERNAME or not MAIL_FROM_ADDRESS:
        print("Email configuration incomplete. OTP printed to console instead.")
        print(f"   OTP for {recipient_email}: {otp_code}")
        return False

    try:
        template = env.get_template("otp_email.html")
        html_content = template.render(otp_code=otp_code)
    except Exception as e:
        print(f"Template Rendering Error: {e}")
        html_content = f"<h3>Your OTP code is: {otp_code}</h3><p>This code will expire in 15 minutes.</p>"

    message = EmailMessage()
    message["From"] = f"{MAIL_FROM_NAME} <{MAIL_FROM_ADDRESS}>"
    message["To"] = recipient_email
    message["Subject"] = "Your To Do List Verification Code"
    message.set_content(html_content, subtype="html")

    try:
        print(f"Sending email to {recipient_email}")
        print(f"   SMTP Host: smtp-relay.brevo.com:{SMTP_PORT}")
        print(f"   Username: {SMTP_USERNAME}")
        print(f"   From: {MAIL_FROM_NAME} <{MAIL_FROM_ADDRESS}>")

        smtp_kwargs = {
            "hostname": "smtp-relay.brevo.com",
            "port": SMTP_PORT,
            "username": SMTP_USERNAME,
            "password": BREVO_SMTP_KEY,
        }

        if SMTP_PORT == 465:
            smtp_kwargs["use_tls"] = True
        else:
            smtp_kwargs["start_tls"] = SMTP_USE_TLS

        await aiosmtplib.send(message, **smtp_kwargs)
        print(f"OTP email sent to {recipient_email}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        print(f"   Error type: {type(e).__name__}")
        return False
