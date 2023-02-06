import requests
import os
from config import config


def send_simple_message(to: str, subject: str, body: str):
    response = requests.post(
        f"https://api.mailgun.net/v3/{config.MAILGUN_DOMAIN}/messages",
        auth=("api", os.getenv("MAILGUN_API_KEY")),
        data={
            "from": f"Jose Salvatierra <mailgun@{config.MAILGUN_DOMAIN}>",
            "to": [to],
            "subject": subject,
            "text": body,
        },
    )
    return response


def send_user_registration_email(email: str, confirmation_url: str):
    return send_simple_message(
        email,
        "Successfully signed up",
        f"Hi {email}! You have successfully signed up to the Stores REST API. Please confirm your email by clicking on the following link: {confirmation_url}",
    )
