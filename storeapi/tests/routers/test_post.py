import pytest
from httpx import AsyncClient

from storeapi import security


async def create_post(
    body: str, async_client: AsyncClient, logged_in_token: str
) -> dict:
    response = await async_client.post(
        "/post",
        json={"body": body},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    return response.json()


async def create_comment(
    body: str, post_id: int, async_client: AsyncClient, logged_in_token: str
) -> dict:
    response = await async_client.post(
        "/comment",
        json={"body": body, "post_id": post_id},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    return response.json()


async def like_post(
    post_id: int, async_client: AsyncClient, logged_in_token: str
) -> dict:
    response = await async_client.post(
        "/like",
        json={"post_id": post_id},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    return response.json()


@pytest.fixture()
async def created_post(async_client: AsyncClient, logged_in_token: str):
    return await create_post("Test Post", async_client, logged_in_token)


@pytest.fixture()
async def created_comment(
    async_client: AsyncClient, created_post: dict, logged_in_token: str
):
    return await create_comment(
        "Test Comment", created_post["id"], async_client, logged_in_token
    )


@pytest.mark.anyio
async def test_create_post(
    async_client: AsyncClient, confirmed_user: dict, logged_in_token: str
):
    body = "Test Post"

    response = await async_client.post(
        "/post",
        json={"body": body},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )

    assert response.status_code == 201
    assert {
        "id": 1,
        "body": body,
        "user_id": confirmed_user["id"],
        "image_url": None,
    }.items() <= response.json().items()


@pytest.mark.anyio
async def test_create_post_expired_token(
    async_client: AsyncClient, confirmed_user: dict, mocker
):
    mocker.patch("storeapi.security.access_token_expire_minutes", return_value=-1)
    token = security.create_access_token(confirmed_user["email"])
    response = await async_client.post(
        "/post",
        json={"body": "Test Post"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert "Token has expired" in response.json()["detail"]


@pytest.mark.anyio
async def test_create_post_missing_data(
    async_client: AsyncClient, logged_in_token: str
):
    response = await async_client.post(
        "/post", json={}, headers={"Authorization": f"Bearer {logged_in_token}"}
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_like_post(
    async_client: AsyncClient, created_post: dict, logged_in_token: str
):
    response = await async_client.post(
        "/like",
        json={"post_id": created_post["id"]},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    assert response.status_code == 201


@pytest.mark.anyio
async def test_create_post_with_prompt(
    async_client: AsyncClient, logged_in_token: str, mock_generate_cute_creature_api
):
    response = await async_client.post(
        "/post?prompt=A cat",
        json={"body": "Test Post"},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    assert response.status_code == 201
    assert {
        "id": 1,
        "body": "Test Post",
        "image_url": None,
    }.items() <= response.json().items()
    mock_generate_cute_creature_api.assert_called()


@pytest.mark.anyio
async def test_get_all_posts(async_client: AsyncClient, created_post: dict):
    response = await async_client.get("/post")

    assert response.status_code == 200
    assert created_post.items() <= response.json()[0].items()


@pytest.mark.anyio
@pytest.mark.parametrize(
    "sorting, expected_order",
    [
        ("new", [2, 1]),
        ("old", [1, 2]),
    ],
)
async def test_get_all_posts_sorting(
    async_client: AsyncClient,
    logged_in_token: str,
    sorting: str,
    expected_order: list[int],
):
    await create_post("Test Post 1", async_client, logged_in_token)
    await create_post("Test Post 2", async_client, logged_in_token)
    response = await async_client.get("/post", params={"sorting": sorting})
    assert response.status_code == 200

    data = response.json()
    post_ids = [post["id"] for post in data]
    assert post_ids == expected_order


@pytest.mark.anyio
async def test_get_all_posts_sort_likes(
    async_client: AsyncClient, logged_in_token: str
):
    await create_post("Test Post 1", async_client, logged_in_token)
    await create_post("Test Post 2", async_client, logged_in_token)
    await like_post(1, async_client, logged_in_token)
    response = await async_client.get("/post", params={"sorting": "most_likes"})
    assert response.status_code == 200

    data = response.json()
    post_ids = [post["id"] for post in data]
    expected_order = [1, 2]
    assert post_ids == expected_order


@pytest.mark.anyio
async def test_get_all_posts_wrong_sorting(async_client: AsyncClient):
    response = await async_client.get("/post", params={"sorting": "wrong"})
    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_comment(
    async_client: AsyncClient,
    created_post: dict,
    confirmed_user: dict,
    logged_in_token: str,
):
    body = "Test Comment"

    response = await async_client.post(
        "/comment",
        json={"body": body, "post_id": created_post["id"]},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    assert response.status_code == 201
    assert {
        "id": 1,
        "body": body,
        "post_id": created_post["id"],
        "user_id": confirmed_user["id"],
    }.items() <= response.json().items()


@pytest.mark.anyio
async def test_get_comments_on_post(
    async_client: AsyncClient, created_post: dict, created_comment: dict
):
    response = await async_client.get(f"/post/{created_post['id']}/comment")

    assert response.status_code == 200
    assert response.json() == [created_comment]


@pytest.mark.anyio
async def test_get_comments_on_post_empty(
    async_client: AsyncClient, created_post: dict
):
    response = await async_client.get(f"/post/{created_post['id']}/comment")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.anyio
async def test_get_post_with_comments(
    async_client: AsyncClient, created_post: dict, created_comment: dict
):
    response = await async_client.get(f"/post/{created_post['id']}")

    assert response.status_code == 200
    assert response.json() == {
        "post": {
            **created_post,
            "likes": 0,
        },
        "comments": [created_comment],
    }


@pytest.mark.anyio
async def test_get_missing_post_with_comments(
    async_client: AsyncClient, created_post: dict, created_comment: dict
):
    response = await async_client.get("/post/2")
    assert response.status_code == 404
