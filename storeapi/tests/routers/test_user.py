import pytest
from fastapi import BackgroundTasks
from httpx import AsyncClient


async def register_user(async_client: AsyncClient, email: str, password: str):
    return await async_client.post(
        "/register", json={"email": email, "password": password}
    )


@pytest.mark.anyio
async def test_register_user(async_client: AsyncClient):
    response = await register_user(async_client, "test@example.net", "1234")
    assert response.status_code == 201
    assert "User created" in response.json()["detail"]


@pytest.mark.anyio
async def test_register_user_already_exists(
    async_client: AsyncClient, registered_user: dict
):
    response = await register_user(
        async_client, registered_user["email"], registered_user["password"]
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


@pytest.mark.anyio
async def test_confirm_user(async_client: AsyncClient, mocker):
    spy = mocker.spy(BackgroundTasks, "add_task")
    await register_user(async_client, "test@example.net", "1234")

    confirmation_url = str(spy.call_args[1]["confirmation_url"])
    response = await async_client.get(confirmation_url)

    assert response.status_code == 200
    assert "User confirmed" in response.json()["detail"]


@pytest.mark.anyio
async def test_confirm_user_invalid_token(async_client: AsyncClient):
    response = await async_client.get("/confirm/invalid_token")
    assert response.status_code == 401


@pytest.mark.anyio
async def test_confirm_user_expired_token(async_client: AsyncClient, mocker):
    mocker.patch("storeapi.security.confirm_token_expire_minutes", return_value=-1)
    spy = mocker.spy(BackgroundTasks, "add_task")
    await register_user(async_client, "test@example.net", "1234")

    confirmation_url = str(spy.call_args[1]["confirmation_url"])
    response = await async_client.get(confirmation_url)

    assert response.status_code == 401
    assert "Token has expired" in response.json()["detail"]


@pytest.mark.anyio
async def test_login_user_not_exists(async_client: AsyncClient):
    response = await async_client.post(
        "/token", json={"email": "test@example.net", "password": "1234"}
    )
    assert response.status_code == 401


@pytest.mark.anyio
async def test_login_user_not_confirmed(
    async_client: AsyncClient, registered_user: dict
):
    response = await async_client.post(
        "/token",
        json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        },
    )
    assert response.status_code == 401


@pytest.mark.anyio
async def test_login_user(async_client: AsyncClient, confirmed_user: dict):
    response = await async_client.post(
        "/token",
        json={"email": confirmed_user["email"], "password": confirmed_user["password"]},
    )
    assert response.status_code == 200
