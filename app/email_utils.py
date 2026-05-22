import os
import smtplib

from email.message import EmailMessage

from dotenv import load_dotenv

load_dotenv()


SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))

SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

SMTP_FROM = os.getenv("SMTP_FROM")


def send_email(
    to_email: str,
    subject: str,
    body: str
):
    if not SMTP_HOST:
        return

    message = EmailMessage()

    message["Subject"] = subject
    message["From"] = SMTP_FROM
    message["To"] = to_email

    message.set_content(body)

    with smtplib.SMTP(
        SMTP_HOST,
        SMTP_PORT
    ) as smtp:

        smtp.starttls()

        smtp.login(
            SMTP_USER,
            SMTP_PASSWORD
        )

        smtp.send_message(message)