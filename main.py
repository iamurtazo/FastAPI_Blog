from contextlib import asynccontextmanager
from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler
from sys import exception
from fastapi import FastAPI, Request, HTTPException , status, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Annotated
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import models
from schemas import (
    UserCreate,
    UserResponse,
    UserUpdate,
    PostCreate,
    PostResponse,
    PostUpdate
)
from database import Base, engine, get_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(lifespan=lifespan)


app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/media", StaticFiles(directory="media"), name="media")

templates = Jinja2Templates(directory="templates")


@app.get("/", include_in_schema=False, name="home")
@app.get("/posts", include_in_schema=False, name="posts")
async def home(request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.Post).order_by(models.Post.options(selectinload(models.Post.author)).date_posted.desc())
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
def not_found_handler(request: Request, exc: HTTPException):
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )

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
def validation_exception_handler(request: Request, exc: RequestValidationError):
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



# USER MODEL ROUTES
@app.post("/api/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED) 
async def create_user(user: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.User).where(models.User.username == user.username)
    )

    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with that {user.username} already exists."
        )
    
    result = await db.execute(
        select(models.User).where(models.User.email == user.email)
    )

    existing_email = result.scalars().first()

    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with that {user.email} already exists."
        )
    
    new_user = models.User(
        username=user.username,
        email = user.email
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@app.get("/api/users/{user_id}", response_model=UserResponse)
async def get_user_api(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found."
        )
    return user


@app.get("/api/users", response_model=list[UserResponse])
async def get_users_api(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.User).order_by(models.User.id.asc())
    )
    users = result.scalars().all()
    return users


@app.get("/api/users/{user_id}/posts", response_model=list[PostResponse])
async def get_user_posts_api(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user=result.scalars().first()


    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found." 
        )
    
    results = await db.execute(
        select(models.Post).where(models.Post.user_id == user_id)
    )
    posts = results.scalars().all()
    return posts


@app.get("/users/{user_id}/posts", include_in_schema=False, name="user_posts")
async def user_posts_page(request: Request, user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user=result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found." 
        )
    
    results = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .where(models.Post.user_id == user_id)
        .order_by(models.Post.date_posted.desc())
    )
    posts = results.scalars().all()

    return templates.TemplateResponse(
        "user_posts.html",
        {
            "request": request,
            "posts": posts,
            "user": user,
            "title": f"Posts by {user.username}"
        }
    )

@app.patch("/api/users/{user_id}", response_model=UserResponse)
async def update_user_full_api(user_id: int, db: Annotated[AsyncSession, Depends(get_db)], user_update_data: UserUpdate):
    result = await db.execute(select(models.User).where(models.User.id == user_id)) 
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found."
        )
    
    if user_update_data.username is not None and user_update_data.username != user.username:
        result = await db.execute(
            select(models.User).where(models.User.username == user_update_data.username)
        )
        existing_user = result.scalars().first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with that {user_update_data.username} already exists."
            )
    if user_update_data.email is not None and user_update_data.email != user.email:
        result = await db.execute(
            select(models.User).where(models.User.email == user_update_data.email)
        )
        existing_user = result.scalars().first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with that {user_update_data.email} already exists."
            )
    
    if user_update_data.username is not None: user.username = user_update_data.username
    if user_update_data.email is not None: user.email = user_update_data.email
    if user_update_data.image_file is not None: user.image_file = user_update_data.image_file

    await db.commit()
    await db.refresh(user)
    return user

@app.delete("/api/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_api(user_id:int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first() 

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found."
        )
    await db.delete(user)
    await db.commit()


# POST MODEL ROUTES
@app.get("/api/posts", response_model=list[PostResponse])
async def get_posts_api(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.Post).order_by(models.Post.date_posted.desc())
    )
    posts = result.scalars().all()
    return posts


@app.post("/api/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(post: PostCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.User).where(models.User.id == post.user_id)
    )
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {post.user_id} not found."
        )
    
    new_post = models.Post(
        title=post.title,
        content=post.content,
        user_id=post.user_id
    )

    db.add(new_post)
    await db.commit()
    await db.refresh(new_post)
    return new_post


@app.get("/api/posts/{post_id}", response_model=PostResponse)
async def get_post_detail_api(post_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).where(models.Post.id == post_id)) 
    post = result.scalars().first()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with ID {post_id} not found."
        )
    return post


@app.put("/api/posts/{post_id}", response_model=PostResponse)
async def update_post_detail_full_api(post_id: int, db: Annotated[AsyncSession, Depends(get_db)], post_data: PostUpdate):
    result = await db.execute(select(models.Post).where(models.Post.id == post_id)) 
    post = result.scalars().first()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with ID {post_id} not found."
        )
    
    if post_data.user_id != post.user_id:
        result = await db.execute(
            select(models.User).where(models.User.id == post_data.user_id)
        )
        user = result.scalars().first()
        if not user: 
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="You do not have permission to update this post."
            )
        
    post.title = post_data.title
    post.content = post_data.content
    post.user_id = post_data.user_id

    await db.commit()
    await db.refresh(post)
    return post

# correct version according to gpt
"""
def update_post_detail_full_api(
    post_id: int,
    post_data: PostUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_user)],
):
    post = db.execute(
        select(models.Post).where(models.Post.id == post_id)
    ).scalars().first()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with ID {post_id} not found."
        )

    if post.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update this post."
        )

    update_data = post_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(post, field, value)

    db.commit()
    db.refresh(post)
    return post

"""

@app.patch("/api/posts/{post_id}", response_model=PostResponse)
async def update_post_detail_partial_api(post_id: int, db: Annotated[AsyncSession, Depends(get_db)], post_data: PostUpdate):
    result = await db.execute(select(models.Post).where(models.Post.id == post_id)) 
    post = result.scalars().first()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with ID {post_id} not found."
        )
    
    update_data = post_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(post, key, value)

    await db.commit()
    await db.refresh(post)
    return post


@app.delete("/api/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post_detail_api(post_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).where(models.Post.id == post_id)) 
    post = result.scalars().first() 

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with ID {post_id} not found."
        )
    await db.delete(post)
    await db.commit()   

@app.get("/posts/{post_id}", response_model=PostResponse, include_in_schema=False, name="post_detail")
async def post_detail(request: Request, post_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .where(models.Post.id == post_id)) 
    post = result.scalars().first()

    if post:
        return templates.TemplateResponse(
            "post_detail.html",
            {
                "request": request,
                "post": post
            }
        )
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Sorry, the post with ID {post_id} does not exist."
    )

