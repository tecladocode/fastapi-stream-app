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
    assert {
        "id": 1,
        "body": "Test Post",
        "image_url": None,
    }.items() <= response.json().items()


@pytest.mark.anyio
async def test_create_post_expired_token(
    async_client: AsyncClient, confirmed_user: dict, mocker
):
    mocker.patch("storeapi.security.access_token_expire_minutes", return_value=-1)
    token = security.create_access_token(confirmed_user["id"])
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
        "/post",
        json={},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_post_with_prompt(
    async_client: AsyncClient, logged_in_token: str, mock_generate_cute_creature_api
):
    response = await async_client.post(
        "/post?prompt=A cat",
        json={"body": "Test Post"},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    logger.info(response.content)
    assert response.status_code == 200
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
    assert response.json() == [
        {
            "id": created_post["id"],
            "body": created_post["body"],
            "user_id": created_post["user_id"],
            "image_url": created_post["image_url"],
            "likes": 0,
        }
    ]


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
    assert [post["id"] for post in data] == expected_order


@pytest.mark.anyio
async def test_get_all_posts_sort_likes(
    async_client: AsyncClient, logged_in_token: str
):
    await create_post("Test Post 1", async_client, logged_in_token)
    await create_post("Test Post 2", async_client, logged_in_token)
    await like_post(2, async_client, logged_in_token)
    response = await async_client.get("/post", params={"sorting": "most_likes"})
    assert response.status_code == 200
    data = response.json()
    assert [post["id"] for post in data] == [2, 1]


@pytest.mark.anyio
async def test_get_all_post_wrong_sorting(async_client: AsyncClient):
    response = await async_client.get("/post", params={"sorting": "wrong"})
    assert response.status_code == 422


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
        "post": {
            "id": created_post["id"],
            "body": created_post["body"],
            "user_id": created_post["user_id"],
            "image_url": created_post["image_url"],
            "likes": 0,
        },
        "comments": [
            {
                "id": created_comment["id"],
                "body": created_comment["body"],
                "post_id": created_comment["post_id"],
                "user_id": created_comment["user_id"],
            }
        ],
    }


@pytest.mark.anyio
async def test_get_missing_post_with_comments(
    async_client: AsyncClient, created_post: dict, created_comment: dict
):
    response = await async_client.get("/post/2")
    assert response.status_code == 404
