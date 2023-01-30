import pytest
from httpx import AsyncClient


@pytest.fixture()
async def registered_user(async_client: AsyncClient):
    user_details = {
        "email": "test@example.net",
        "password": "1234"
    }
    await async_client.post("/register", json=user_details)
    return user_details


@pytest.mark.anyio
@pytest.mark.skip()
async def test_register_user(async_client: AsyncClient):
    response = await async_client.post("/register", json={
        "email": "test@example.net",
        "password": "1234"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.anyio
async def test_register_already_exists(async_client: AsyncClient, registered_user: dict):
    response = await async_client.post("/register", json=registered_user)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


@pytest.mark.anyio
@pytest.mark.skip()
async def test_login_user_not_exists(async_client: AsyncClient):
    response = await async_client.post("/token", json={
        "email": "test@example.net",
        "password": "1234"
    })
    assert response.status_code == 401


@pytest.mark.anyio
@pytest.mark.skip()
async def test_login_user(async_client: AsyncClient, registered_user: dict):
    response = await async_client.post("/token", json={
        "email": registered_user["email"],
        "password": registered_user["password"]
    })
    assert response.status_code == 200