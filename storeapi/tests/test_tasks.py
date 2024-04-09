import httpx
import pytest
from databases import Database
from storeapi.database import database, post_table
from storeapi.tasks import (
    APIResponseError,
    _generate_cute_creature_api,
    generate_and_add_to_post,
    send_simple_email,
)


@pytest.mark.anyio
async def test_send_simple_email(mock_httpx_client):
    await send_simple_email("test@example.net", "Test Subject", "Test Body")
    mock_httpx_client.post.assert_called()


@pytest.mark.anyio
async def test_send_simple_email_api_error(mock_httpx_client):
    mock_httpx_client.post.return_value = httpx.Response(
        status_code=500, content="", request=httpx.Request("POST", "//")
    )

    with pytest.raises(APIResponseError):
        await send_simple_email("test@example.net", "Test Subject", "Test Body")


@pytest.mark.asyncio
async def test_generate_cute_creature_api_success(mock_httpx_client):
    json_data = {"output_url": "https://example.com/image.jpg"}

    mock_httpx_client.post.return_value = httpx.Response(
        status_code=200, json=json_data, request=httpx.Request("POST", "//")
    )

    result = await _generate_cute_creature_api("A cat")

    assert result == json_data


@pytest.mark.asyncio
async def test_generate_cute_creature_api_server_error(mock_httpx_client):
    mock_httpx_client.post.return_value = httpx.Response(
        status_code=500, content="", request=httpx.Request("POST", "//")
    )

    with pytest.raises(
        APIResponseError, match="API request failed with status code 500"
    ):
        await _generate_cute_creature_api("A cat")


@pytest.mark.asyncio
async def test_generate_cute_creature_api_json_error(mock_httpx_client):
    mock_httpx_client.post.return_value = httpx.Response(
        status_code=200, content="Not JSON", request=httpx.Request("POST", "//")
    )

    with pytest.raises(APIResponseError, match="API response parsing failed"):
        await _generate_cute_creature_api("A cat")


@pytest.mark.asyncio
async def test_generate_and_add_to_post_success(
    mock_httpx_client, created_post: dict, confirmed_user: dict, db: Database
):
    json_data = {"output_url": "https://example.com/image.jpg"}

    mock_httpx_client.post.return_value = httpx.Response(
        status_code=200, json=json_data, request=httpx.Request("POST", "//")
    )

    await generate_and_add_to_post(
        confirmed_user["email"], created_post["id"], "/post/1", db, "A cat"
    )

    # Check that after the background task runs, the post has been updated
    query = post_table.select().where(post_table.c.id == created_post["id"])

    updated_post = await database.fetch_one(query)

    assert updated_post.image_url == json_data["output_url"]
