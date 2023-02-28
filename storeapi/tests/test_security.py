import pytest
from jose import jwt

from storeapi import security


@pytest.mark.anyio
def test_access_token_expire_minutes():
    assert security.access_token_expire_minutes() == 30


def test_confirm_token_expire_minutes():
    assert security.confirm_token_expire_minutes() == 1440


def test_create_access_token():
    token = security.create_access_token("123")
    assert {"sub": "123"}.items() <= jwt.decode(
        token, security.SECRET_KEY, algorithms=[security.ALGORITHM]
    ).items()


def test_create_confirmation_token():
    email = "test@example.com"
    token = security.create_confirmation_token(email)
    assert {"sub": email}.items() <= jwt.decode(
        token, security.SECRET_KEY, algorithms=[security.ALGORITHM]
    ).items()


def test_get_email_from_confirmation_token():
    email = "test@example.com"
    token = security.create_confirmation_token(email)
    assert security.get_email_from_confirmation_token(token) == email


def test_password_hashes():
    password = "password"
    assert security.verify_password(password, security.get_password_hash(password))


@pytest.mark.anyio
async def test_get_user(registered_user: dict):
    user = await security.get_user(registered_user["email"])
    assert user.email == registered_user["email"]


@pytest.mark.anyio
async def test_get_user_not_found():
    user = await security.get_user("test@example.com")
    assert user is None


@pytest.mark.anyio
async def test_authenticate_user(confirmed_user: dict):
    user = await security.authenticate_user(
        confirmed_user["email"], confirmed_user["password"]
    )
    assert user.email == confirmed_user["email"]


@pytest.mark.anyio
async def test_authenticate_user_not_found():
    with pytest.raises(security.HTTPException):
        await security.authenticate_user("test@example.com", "1234")


@pytest.mark.anyio
async def test_authenticate_user_wrong_password(confirmed_user: dict):
    with pytest.raises(security.HTTPException):
        await security.authenticate_user(confirmed_user["email"], "wrong password")


@pytest.mark.anyio
async def test_authenticate_user_not_confirmed(registered_user: dict):
    with pytest.raises(security.HTTPException):
        await security.authenticate_user(
            registered_user["email"], registered_user["password"]
        )


@pytest.mark.anyio
async def test_get_current_user(confirmed_user: dict):
    token = security.create_access_token(confirmed_user["email"])
    user = await security.get_current_user(token)
    assert user.email == confirmed_user["email"]


@pytest.mark.anyio
async def test_get_current_user_invalid_token():
    with pytest.raises(security.HTTPException):
        await security.get_current_user("invalid token")
