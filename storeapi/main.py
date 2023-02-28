import logging

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI, HTTPException
from fastapi.exception_handlers import http_exception_handler

from storeapi.database import database
from storeapi.logging_conf import configure_logging
from storeapi.routers.posts import router as posts_router
from storeapi.routers.upload import router as upload_router
from storeapi.routers.user import router as user_router

logger = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(CorrelationIdMiddleware)
app.include_router(upload_router)
app.include_router(user_router)
app.include_router(posts_router)


@app.exception_handler(HTTPException)
async def http_exception_handle_logging(request, exc):
    logger.error(f"HTTPException: {exc.status_code} {exc.detail}")
    return await http_exception_handler(request, exc)


@app.on_event("startup")
async def startup():
    configure_logging()
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()
