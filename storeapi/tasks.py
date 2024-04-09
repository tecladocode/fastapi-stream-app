import logging
from json import JSONDecodeError

import httpx
from databases import Database
from storeapi.config import config
from storeapi.database import post_table

logger = logging.getLogger(__name__)


class APIResponseError(Exception):
    pass


async def send_simple_email(to: str, subject: str, body: str):
    logger.debug(f"Sending email to '{to[:3]}' with subject '{subject[:20]}'")
    async with httpx.AsyncClient() as client:
        try:
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
            response.raise_for_status()

            logger.debug(response.content)

            return response
        except httpx.HTTPStatusError as err:
            raise APIResponseError(
                f"API request failed with status code {err.response.status_code}"
            ) from err


async def send_user_registration_email(email: str, confirmation_url: str):
    return await send_simple_email(
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
        try:
            response = await client.post(
                "https://api.deepai.org/api/cute-creature-generator",
                data={"text": prompt},
                headers={"api-key": config.DEEPAI_API_KEY},
                timeout=60,
            )
            logger.debug(response)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as err:
            raise APIResponseError(
                f"API request failed with status code {err.response.status_code}"
            ) from err
        except (JSONDecodeError, TypeError) as err:
            raise APIResponseError("API response parsing failed") from err


async def generate_and_add_to_post(
    email: str,
    post_id: int,
    post_url: str,
    database: Database,
    prompt: str = "A blue british shorthair cat is sitting on a couch",
):
    try:
        response = await _generate_cute_creature_api(prompt)
    except APIResponseError:
        return await send_simple_email(
            email,
            "Error generating image",
            (
                f"Hi {email}! Unfortunately there was an error generating an image"
                "for your post."
            ),
        )

    logger.debug("Connecting to database to update post")

    query = (
        post_table.update()
        .where(post_table.c.id == post_id)
        .values(image_url=response["output_url"])
    )

    logger.debug(query)

    await database.execute(query)

    logger.debug("Database connection in background task closed")

    await send_simple_email(
        email,
        "Image generation completed",
        (
            f"Hi {email}! Your image has been generated and added to your post."
            f" Please click on the following link to view it: {post_url}"
        ),
    )
    return response
