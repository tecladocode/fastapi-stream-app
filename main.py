from fastapi import FastAPI, HTTPException, status, Depends, BackgroundTasks
from database import database, post_table, user_table, comments_table
from models.post import UserPost, UserPostIn, Comment, CommentIn, UserPostWithComments
from models.user import User, UserIn
from security import (
    get_password_hash,
    create_access_token,
    authenticate_user,
    get_current_user,
)
import tasks

app = FastAPI()


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.post("/post", response_model=UserPost)
async def create_post(post: UserPostIn, current_user: User = Depends(get_current_user)):
    data = {**post.dict(), "user_id": current_user.id}
    query = post_table.insert().values(data)
    last_record_id = await database.execute(query)
    return {**data, "id": last_record_id}


@app.get("/posts", response_model=list[UserPost])
async def get_all_posts():
    query = post_table.select()
    return await database.fetch_all(query)


@app.post("/register")
async def register(user: UserIn, background_tasks: BackgroundTasks):
    hashed_password = get_password_hash(user.password)
    query = user_table.insert().values(username=user.username, email=user.email, password=hashed_password)
    await database.execute(query)
    background_tasks.add_task(tasks.send_user_registration_email, user.email, user.username)
    access_token = create_access_token(user.username)
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/token")
async def login(user: UserIn):
    user = await authenticate_user(user.username, user.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(user.username)
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/comment", response_model=Comment)
async def create_comment(
    comment: CommentIn, current_user: User = Depends(get_current_user)
):
    data = {**comment.dict(), "user_id": current_user.id}
    query = comments_table.insert().values(data)
    last_record_id = await database.execute(query)
    return {**data, "id": last_record_id}


@app.get("/post/{post_id}/comments", response_model=list[Comment])
async def get_comments_on_post(post_id: int):
    query = comments_table.select().where(comments_table.c.post_id == post_id)
    return await database.fetch_all(query)


@app.get("/posts/{post_id}", response_model=UserPostWithComments)
async def get_post_with_comments(post_id: int):
    query = post_table.select().where(post_table.c.id == post_id)
    post = await database.fetch_one(query)
    query = comments_table.select().where(comments_table.c.post_id == post_id)
    comments = await database.fetch_all(query)
    return {**post, "comments": comments}
