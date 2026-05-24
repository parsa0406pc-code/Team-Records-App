import os
import requests
from dotenv import load_dotenv

load_dotenv()

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
RESEND_FROM = os.getenv("RESEND_FROM", "onboarding@resend.dev")


def send_email(to_email: str, subject: str, body: str):
    if not RESEND_API_KEY:
        print("RESEND_API_KEY is missing")
        return

    response = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "from": RESEND_FROM,
            "to": [to_email],
            "subject": subject,
            "text": body,
        },
        timeout=8,
    )

    if response.status_code >= 400:
        print("EMAIL ERROR:", response.status_code, response.text)