from fastapi import FastAPI
from database import database
from router.upload import router as upload_router
from router.user import router as user_router
from router.posts import router as posts_router

app = FastAPI()
app.include_router(upload_router)
app.include_router(user_router)
app.include_router(posts_router)


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()
