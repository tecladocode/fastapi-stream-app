import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_register_user(async_client: AsyncClient):
    response = await async_client.post(
        "/register", json={"email": "test@example.net", "password": "1234"}
    )
    assert response.status_code == 200
    assert "User created" in response.json()["message"]


@pytest.mark.anyio
async def test_register_already_exists(
    async_client: AsyncClient, registered_user: dict
):
    response = await async_client.post("/register", json=registered_user)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


@pytest.mark.anyio
async def test_login_user_not_exists(async_client: AsyncClient):
    response = await async_client.post(
        "/token", json={"email": "test@example.net", "password": "1234"}
    )
    assert response.status_code == 401


@pytest.mark.anyio
async def test_login_user(async_client: AsyncClient, confirmed_user: dict):
    response = await async_client.post(
        "/token",
        json={"email": confirmed_user["email"], "password": confirmed_user["password"]},
    )
    assert response.status_code == 200
