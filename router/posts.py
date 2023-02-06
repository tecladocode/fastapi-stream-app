from fastapi import APIRouter, Depends
from database import database, post_table, comments_table
from models.post import UserPost, UserPostIn, Comment, CommentIn, UserPostWithComments
from models.user import User
from security import get_current_user


router = APIRouter()


@router.post("/post", response_model=UserPost)
async def create_post(post: UserPostIn, current_user: User = Depends(get_current_user)):
    data = {**post.dict(), "user_id": current_user.id}
    query = post_table.insert().values(data)
    last_record_id = await database.execute(query)
    return {**data, "id": last_record_id}


@router.get("/post", response_model=list[UserPost])
async def get_all_posts():
    query = post_table.select()
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
    query = post_table.select().where(post_table.c.id == post_id)
    post = await database.fetch_one(query)
    query = comments_table.select().where(comments_table.c.post_id == post_id)
    comments = await database.fetch_all(query)
    return {**post, "comments": comments}
