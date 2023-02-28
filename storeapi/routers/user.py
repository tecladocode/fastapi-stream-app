import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status
from jose import ExpiredSignatureError, JWTError

from storeapi import tasks
from storeapi.database import database, user_table
from storeapi.models.user import UserIn
from storeapi.security import (
    authenticate_user,
    create_access_token,
    create_confirmation_token,
    get_email_from_confirmation_token,
    get_password_hash,
    get_user,
)

logger = logging.getLogger(__name__)
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
    logger.debug("Submitting background task to send email")
    background_tasks.add_task(
        tasks.send_user_registration_email,
        user.email,
        confirmation_url=request.url_for(
            "confirm_email", token=create_confirmation_token(user.email)
        ),
    )
    return {"detail": "User created. Please confirm your email."}


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
        return {"detail": "User confirmed"}
    except ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Token has expired.")
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid token.")
