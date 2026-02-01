from sys import exception
from fastapi import FastAPI, Request, HTTPException , status, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Annotated
from sqlalchemy import select
from sqlalchemy.orm import Session
import models
from schemas import *
from database import Base, engine, get_db

Base.metadata.create_all(bind=engine)


app = FastAPI()


app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/media", StaticFiles(directory="media"), name="media")

templates = Jinja2Templates(directory="templates")


@app.get("/", include_in_schema=False, name="home")
@app.get("/posts", include_in_schema=False, name="posts")
def home(request: Request, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(
        select(models.Post).order_by(models.Post.date_posted.desc())
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
def create_user(user: UserCreate, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(
        select(models.User).where(models.User.username == user.username)
    )

    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with that {user.username} already exists."
        )
    
    result = db.execute(
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
def get_user_api(user_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found."
        )
    return user


@app.get("/api/users/{user_id}/posts", response_model=list[PostResponse])
def get_user_posts_api(user_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(models.User.id == user_id))
    user=result.scalars().first()


    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found." 
        )
    
    results = db.execute(
        select(models.Post).where(models.Post.user_id == user_id)
    )
    posts = results.scalars().all()
    return posts


@app.get("/users/{user_id}/posts", include_in_schema=False, name="user_posts")
def user_posts_page(request: Request, user_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(models.User.id == user_id))
    user=result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found." 
        )
    
    results = db.execute(
        select(models.Post).where(models.Post.user_id == user_id).order_by(models.Post.date_posted.desc())
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



# POST MODEL ROUTES
@app.get("/api/posts", response_model=list[PostResponse])
def get_posts_api(db: Annotated[Session, Depends(get_db)]):
    result = db.execute(
        select(models.Post).order_by(models.Post.date_posted.desc())
    )
    posts = result.scalars().all()
    return posts


@app.post("/api/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(post: PostCreate, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(
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
    db.commit()
    db.refresh(new_post)
    return new_post


@app.get("/api/posts/{post_id}", response_model=PostResponse)
def get_post_detail_api(post_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post).where(models.Post.id == post_id)) 
    post = result.scalars().first()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with ID {post_id} not found."
        )
    return post


@app.put("/api/posts/{post_id}", response_model=PostResponse)
def update_post_detail_full_api(post_id: int, db: Annotated[Session, Depends(get_db)], post_data: PostCreate):
    result = db.execute(select(models.Post).where(models.Post.id == post_id)) 
    post = result.scalars().first()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with ID {post_id} not found."
        )
    
    if post_data.user_id != post.user_id:
        result = db.execute(
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

    db.commit()
    db.refresh(post)
    return post


@app.patch("/api/posts/{post_id}", response_model=PostResponse)
def update_post_detail_partial_api(post_id: int, db: Annotated[Session, Depends(get_db)], post_data: PostUpdate):
    result = db.execute(select(models.Post).where(models.Post.id == post_id)) 
    post = result.scalars().first()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with ID {post_id} not found."
        )
    
    update_date = post_data.model_dump(exclude_unset=True)
    for key, value in update_date.items():
        setattr(post, key, value)

    db.commit()
    db.refresh(post)
    return post


@app.delete("/api/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post_detail_api(post_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post).where(models.Post.id == post_id)) 
    post = result.scalars().first() 

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with ID {post_id} not found."
        )
    db.delete(post)
    db.commit() 


@app.get("/posts/{post_id}", response_model=PostResponse, include_in_schema=False, name="post_detail")
def post_detail(request: Request, post_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post).where(models.Post.id == post_id)) 
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

