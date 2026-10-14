"""Sending email. The only file that knows which email provider we use (Resend today).

Routes call send_email(); swapping providers later means changing this file and nothing else.
"""

import os

import resend
from dotenv import load_dotenv

load_dotenv()

# Until you own a domain, Resend only sends from its test address, and only to your own inbox.
DEFAULT_FROM = "Huntboard <onboarding@resend.dev>"


class EmailNotSent(Exception):
    """The provider refused or failed to send. The caller decides what the user sees."""


def send_email(to: str, subject: str, text: str) -> None:
    # Read at call time (not import time) so tests and a changed .env take effect.
    api_key = os.getenv("RESEND_API_KEY")

    if not api_key:
        # Production must never fall back to printing: anyone who can read the
        # server logs could then copy a verification or reset code.
        if os.getenv("APP_ENV") == "production":
            raise EmailNotSent("RESEND_API_KEY is not set in production")
        print(f"\n--- EMAIL (dev mode, not sent) ---\nTo: {to}\nSubject: {subject}\n\n{text}\n----------------------------------\n")
        return

    resend.api_key = api_key
    try:
        resend.Emails.send({
            "from": os.getenv("EMAIL_FROM", DEFAULT_FROM),
            "to": [to],
            "subject": subject,
            "text": text,
        })
    except resend.exceptions.ResendError as error:
        raise EmailNotSent(str(error)) from error
