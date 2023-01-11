from pydantic import BaseModel


class User(BaseModel):
    id: int | None = None
    username: str
    email: str


class UserIn(User):
    password: str
