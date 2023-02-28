import pytest

from storeapi.tasks import send_simple_message


@pytest.mark.anyio
async def test_send_simple_message(mock_httpx_client):
    await send_simple_message("test@example.net", "Test Subject", "Test Body")
    mock_httpx_client.post.assert_called()
