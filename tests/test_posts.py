import pytest
from httpx import AsyncClient


@pytest.fixture()
async def created_post(async_client: AsyncClient, logged_in_token: str):
    response = await async_client.post(
        "/post",
        json={"body": "Test Post"},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    return response.json()


@pytest.fixture()
async def created_comment(
    async_client: AsyncClient, created_post: dict, logged_in_token: str
):
    response = await async_client.post(
        "/comment",
        json={"body": "Test Comment", "post_id": created_post["id"]},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    return response.json()


@pytest.mark.anyio
async def test_create_post(async_client: AsyncClient, logged_in_token: str):
    response = await async_client.post(
        "/post",
        json={"body": "Test Post"},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    assert response.status_code == 200
    assert {"id": 1, "body": "Test Post"}.items() <= response.json().items()


@pytest.mark.anyio
async def test_get_all_posts(async_client: AsyncClient, created_post: dict):
    response = await async_client.get("/post")
    assert response.status_code == 200
    assert response.json() == [
        {
            "id": created_post["id"],
            "body": created_post["body"],
            "user_id": created_post["user_id"],
        }
    ]


@pytest.mark.anyio
async def test_create_comment(
    async_client: AsyncClient,
    created_post: dict,
    logged_in_token: str,
):
    response = await async_client.post(
        "/comment",
        json={"body": "Test Comment", "post_id": created_post["id"]},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    assert response.status_code == 200
    assert {
        "id": 1,
        "body": "Test Comment",
        "post_id": created_post["id"],
    }.items() <= response.json().items()


@pytest.mark.anyio
async def test_get_comments_on_post(
    async_client: AsyncClient, created_post: dict, created_comment: dict
):
    response = await async_client.get(f"/post/{created_post['id']}/comment")
    assert response.status_code == 200
    assert response.json() == [
        {
            "id": created_comment["id"],
            "body": created_comment["body"],
            "post_id": created_comment["post_id"],
            "user_id": created_comment["user_id"],
        }
    ]


@pytest.mark.anyio
async def test_get_post_with_comments(
    async_client: AsyncClient, created_post: dict, created_comment: dict
):
    response = await async_client.get(f"/post/{created_post['id']}")
    assert response.status_code == 200
    assert response.json() == {
        "id": created_post["id"],
        "body": created_post["body"],
        "user_id": created_post["user_id"],
        "comments": [
            {
                "id": created_comment["id"],
                "body": created_comment["body"],
                "post_id": created_comment["post_id"],
                "user_id": created_comment["user_id"],
            }
        ],
    }
