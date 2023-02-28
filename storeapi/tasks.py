import logging

import httpx

from storeapi.config import config
from storeapi.database import database, post_table

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


async def send_simple_message(to: str, subject: str, body: str):
    logger.debug(f"Sending email to '{to[:3]}' with subject '{subject[:20]}'")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://api.mailgun.net/v3/{config.MAILGUN_DOMAIN}/messages",
            auth=("api", config.MAILGUN_API_KEY),
            data={
                "from": f"Jose Salvatierra <mailgun@{config.MAILGUN_DOMAIN}>",
                "to": [to],
                "subject": subject,
                "text": body,
            },
        )
        logger.debug(response.content)
    return response


async def send_user_registration_email(email: str, confirmation_url: str):
    return await send_simple_message(
        email,
        "Successfully signed up",
        (
            f"Hi {email}! You have successfully signed up to the Stores REST API."
            " Please confirm your email by clicking on the"
            f" following link: {confirmation_url}"
        ),
    )


async def _generate_cute_creature_api(prompt: str):
    logger.debug("Generating cute creature")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.deepai.org/api/cute-creature-generator",
            data={"text": prompt},
            headers={"api-key": "quickstart-QUdJIGlzIGNvbWluZy4uLi4K"},
            timeout=60,
        )
        logger.debug(response)
        return response.json()


async def generate_and_add_to_post(
    email: str,
    post_id: int,
    post_url: str,
    prompt: str = "A blue british shorthair cat is sitting on a couch",
):
    response = await _generate_cute_creature_api(prompt)
    logger.debug("Connecting to database to update post")
    await database.connect()
    query = (
        post_table.update()
        .where(post_table.c.id == post_id)
        .values(image_url=response["output_url"])
    )
    await database.execute(query)
    await database.disconnect()
    logger.debug("Database connection in background task closed")
    return await send_simple_message(
        email,
        "Image generation completed",
        (
            f"Hi {email}! Your image has been generated and added to your post."
            f" Please click on the following link to view it: {post_url}"
        ),
    )
