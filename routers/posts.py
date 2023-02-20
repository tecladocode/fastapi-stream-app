from enum import Enum

import sqlalchemy
from fastapi import APIRouter, BackgroundTasks, Depends, Request

from database import comments_table, database, likes_table, post_table
from models.post import (
    Comment,
    CommentIn,
    PostLike,
    PostLikeIn,
    UserPost,
    UserPostIn,
    UserPostWithComments,
    UserPostWithLikes,
)
from models.user import User
from security import get_current_user
from tasks import generate_and_add_to_post

router = APIRouter()


@router.post("/post", response_model=UserPost)
async def create_post(
    post: UserPostIn,
    background_tasks: BackgroundTasks,
    request: Request,
    prompt: str = None,
    current_user: User = Depends(get_current_user),
):
    data = {**post.dict(), "user_id": current_user.id}
    query = post_table.insert().values(data)
    last_record_id = await database.execute(query)
    if prompt:
        background_tasks.add_task(
            generate_and_add_to_post,
            current_user.email,
            last_record_id,
            request.url_for("get_post_with_comments", post_id=last_record_id),
            prompt,
        )
    return {**data, "id": last_record_id}


class PostSorting(str, Enum):
    new = "new"
    old = "old"
    most_likes = "most_likes"


@router.get("/post", response_model=list[UserPostWithLikes])
async def get_all_posts(sorting: PostSorting = PostSorting.new):
    query = (
        sqlalchemy.select(
            post_table, sqlalchemy.func.count(likes_table.c.id).label("likes")
        )
        .select_from(post_table.outerjoin(likes_table))
        .group_by(post_table.c.id)
    )

    if sorting == PostSorting.new:
        query = query.order_by(post_table.c.id.desc())
    elif sorting == PostSorting.old:
        query = query.order_by(post_table.c.id.asc())
    elif sorting == PostSorting.most_likes:
        query = query.order_by(sqlalchemy.desc("likes"))

    return await database.fetch_all(query)


@router.post("/comment", response_model=Comment)
async def create_comment(
    comment: CommentIn, current_user: User = Depends(get_current_user)
):
    data = {**comment.dict(), "user_id": current_user.id}
    query = comments_table.insert().values(data)
    last_record_id = await database.execute(query)
    return {**data, "id": last_record_id}


@router.get("/post/{post_id}/comment", response_model=list[Comment])
async def get_comments_on_post(post_id: int):
    query = comments_table.select().where(comments_table.c.post_id == post_id)
    return await database.fetch_all(query)


@router.get("/post/{post_id}", response_model=UserPostWithComments)
async def get_post_with_comments(post_id: int):
    query = (
        sqlalchemy.select(
            post_table, sqlalchemy.func.count(likes_table.c.id).label("likes")
        )
        .select_from(post_table.outerjoin(likes_table))
        .where(post_table.c.id == post_id)
        .group_by(post_table.c.id)
    )
    post = await database.fetch_one(query)
    return {"post": post, "comments": await get_comments_on_post(post_id)}


@router.post("/like", response_model=PostLike)
async def like_post(like: PostLikeIn, current_user: User = Depends(get_current_user)):
    data = {**like.dict(), "user_id": current_user.id}
    query = likes_table.insert().values(data)
    last_record_id = await database.execute(query)
    return {**data, "id": last_record_id}
