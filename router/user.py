from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Request
from database import database, user_table
from models.user import UserIn
from security import (
    get_password_hash,
    create_access_token,
    create_confirmation_token,
    get_email_from_confirmation_token,
    authenticate_user,
    get_user,
)
from jose import JWTError, ExpiredSignatureError
import tasks


router = APIRouter()


@router.post("/register")
async def register(user: UserIn, background_tasks: BackgroundTasks, request: Request):
    if await get_user(user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with that email already exists",
        )

    hashed_password = get_password_hash(user.password)
    query = user_table.insert().values(email=user.email, password=hashed_password)
    await database.execute(query)
    background_tasks.add_task(
        tasks.send_user_registration_email,
        user.email,
        confirmation_url=request.url_for(
            "confirm_email", token=create_confirmation_token(user.email)
        ),
    )
    return {"message": "User created. Please confirm your email."}


@router.post("/token")
async def login(user: UserIn):
    user = await authenticate_user(user.email, user.password)
    access_token = create_access_token(user.email)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/confirm/{token}")
async def confirm_email(token: str):
    try:
        email = get_email_from_confirmation_token(token)
        query = (
            user_table.update()
            .where(user_table.c.email == email)
            .values(confirmed=True)
        )
        await database.execute(query)
        return {"detail": "Email confirmed"}
    except ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Token has expired.")
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid token.")
