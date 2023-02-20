import logging
import logging.config

from fastapi import FastAPI

from database import database
from routers.posts import router as posts_router
from routers.upload import router as upload_router
from routers.user import router as user_router

logging.config.fileConfig("logging.conf", disable_existing_loggers=False)


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
