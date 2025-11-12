from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.error_handler import ErrorHandlerMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.database import db, Base, engine, close_engine, close_mongo_connection
from app.core.redis import clear_permissions_cache, close_redis
from fastapi.responses import HTMLResponse
from app import main
from templates import swagger
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    """Create database tables and start Redis connection on FastAPI startup,
    and close them on shutdown."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await clear_permissions_cache()

    yield  # <--- app runs while this yields

    # Shutdown
    await close_mongo_connection()
    await close_redis()
    await close_engine()
    
    """
    Initialize Fastapi with swagger redirect url to hanle custom login
    """
app = FastAPI(
    title=settings.PROJECT_NAME,
    servers=[{"url": "http://localhost:8000"}],
    swagger_ui_oauth2_redirect_url="/docs/oauth2-redirect",
    docs_url=None,
    lifespan=lifespan
)

""" Added CORS Middle ware to allow cross origin resouce sharing
    Currently in development so allowed all origins, methods, headers, with credentials
"""
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

"""Custom middle to print meta data of request and computation time for each request"""
app.add_middleware(RequestLoggingMiddleware)

"""Custom error handler middle ware"""
app.add_middleware(ErrorHandlerMiddleware)

"""Adding all the routes to FastAPI instance"""
app.include_router(main.router)


"""Over ridding inbuilt swagger/ui to add drop down for filtering routes based on tags"""
@app.get("/docs", include_in_schema=False)
def custom_docs():
    return HTMLResponse(content=swagger.html)


@app.get("/",tags=["Root"])
async def root():
    return {"message": f"{settings.PROJECT_NAME} is running"}


