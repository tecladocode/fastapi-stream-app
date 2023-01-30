import requests
import os
from dotenv import load_dotenv

load_dotenv()

DOMAIN = os.getenv("MAILGUN_DOMAIN")

def send_simple_message(to: str, subject: str, body: str):
    response = requests.post(
        f"https://api.mailgun.net/v3/{DOMAIN}/messages",
        auth=("api", os.getenv("MAILGUN_API_KEY")),
        data={
            "from": f"Jose Salvatierra <mailgun@{DOMAIN}>",
            "to": [to],
            "subject": subject,
            "text": body
        },
    )
    return response


def send_user_registration_email(email: str):
    return send_simple_message(
        email,
        "Successfully signed up",
        f"Hi {email}! You have successfully signed up to the Stores REST API."
    )