# Standard library imports
from contextlib import asynccontextmanager
from typing import Annotated

# Third-party imports
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import http_exception_handler
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

# Local application imports
import models
from database import Base, engine, get_db
from routers.api import users as api_users, posts as api_posts
from routers.web import users as web_users, posts as web_posts, auth as web_auth

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(lifespan=lifespan)

# Include API routers
app.include_router(api_users.router)
app.include_router(api_posts.router)

# Include Web routers
app.include_router(web_users.router)
app.include_router(web_posts.router)
app.include_router(web_auth.router)

# Mount static and media directories
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/media", StaticFiles(directory="media"), name="media")

# Templates setup
templates = Jinja2Templates(directory="templates")


@app.get("/", include_in_schema=False, name="home")
@app.get("/posts", include_in_schema=False, name="posts")
async def home(request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .order_by(models.Post.date_posted.desc())
    )
    posts = result.scalars().all()
    return templates.TemplateResponse(
        request, 
        'home.html', 
        {
            "request": request, 
            "posts": posts,
            "title": "Home Page"
        }
    )



# EXCEPTION HANDLERS
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    if request.url.path.startswith("/api"):
        return await http_exception_handler(request, exc)

    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "error_title": "Page Not Found",
            "error_message": exc.detail,
            "home_link": "/posts",
            "status_code": exc.status_code
        },
        status_code=404
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "error_title": "Invalid Request",
            "error_message": "The page you're looking for doesn't exist or the URL is invalid.",
            "home_link": "/posts"
        },
        status_code=422
    )