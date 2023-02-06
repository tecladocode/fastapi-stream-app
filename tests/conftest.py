import os
from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

os.environ["ENV_STATE"] = "test"

from database import database, user_table
from main import app


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture()
def client() -> Generator:
    yield TestClient(app)


@pytest.fixture(autouse=True, scope="function")
async def db() -> AsyncGenerator:
    await database.connect()
    yield
    await database.disconnect()


@pytest.fixture()
async def async_client(client) -> AsyncGenerator:
    async with AsyncClient(app=app, base_url=client.base_url) as ac:
        yield ac


# Mock the tasks send_simple_message function so that it doesn't actually send emails
@pytest.fixture(autouse=True)
def mock_send_simple_message(mocker):
    return mocker.patch("tasks.send_simple_message")


@pytest.fixture()
async def confirmed_user(registered_user: dict):
    query = (
        user_table.update()
        .where(user_table.c.email == registered_user["email"])
        .values(confirmed=True)
    )
    await database.execute(query)
    return registered_user


@pytest.fixture()
async def registered_user(async_client: AsyncClient):
    user_details = {"email": "test@example.net", "password": "1234"}
    await async_client.post("/register", json=user_details)
    return user_details


@pytest.fixture()
async def logged_in_token(async_client: AsyncClient, confirmed_user: dict):
    response = await async_client.post("/token", json=confirmed_user)
    return response.json()["access_token"]
