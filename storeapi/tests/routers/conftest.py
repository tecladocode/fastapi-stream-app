import pytest
from httpx import AsyncClient


@pytest.fixture()
def mock_generate_cute_creature_api(mocker):
    return mocker.patch(
        "storeapi.tasks._generate_cute_creature_api",
        return_value={"output_url": "http://example.net"},
    )


@pytest.fixture()
async def logged_in_token(async_client: AsyncClient, confirmed_user: dict):
    response = await async_client.post("/token", json=confirmed_user)
    return response.json()["access_token"]
