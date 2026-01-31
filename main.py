from sys import exception
from fastapi import FastAPI, Request, HTTPException , status
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from schemas import PostCreate, PostResponse

app = FastAPI()


app.mount("/static", StaticFiles(directory="static"), name="static")


templates = Jinja2Templates(directory="templates")


posts = [
    {
        "id": 1,
        "author": "Alice",
        "title": "First Post",
        "content": "This is the content of the first post.",
        "date_posted": "2026-01-25"
    },
    {
        "id": 2,
        "author": "Bob",
        "title": "Second Post",
        "content": "This is the content of the second post.",
        "date_posted": "2026-01-26"
    },
    {
        "id": 3,
        "author": "Charlie",
        "title": "Third Post",
        "content": "This is the content of the third post.",
        "date_posted": "2026-01-27"
    },
    {
        "id": 4,
        "author": "Diana",
        "title": "Fourth Post",
        "content": "This is the content of the fourth post.",
        "date_posted": "2026-01-28"
    },
    {
        "id": 5,
        "author": "Eve",
        "title": "Fifth Post",
        "content": "This is the content of the fifth post.",
        "date_posted": "2026-01-29"
    }
]


@app.get("/", include_in_schema=False)
@app.get("/posts", include_in_schema=False)
def home(request: Request):
    return templates.TemplateResponse(
        request, 
        'home.html', 
        {
            "request": request, 
            "posts": posts,
            "title": "Home Page"
        }
    )

@app.get("/api/posts", response_model=list[PostResponse])
def get_posts_api():
    return posts

@app.exception_handler(404)
def not_found_handler(request: Request, exc: HTTPException):
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


# post-detail endpoint
@app.get("/posts/{post_id}", response_model=PostResponse)
def get_post(request: Request, post_id: int): 
    for post in posts:
        if post["id"] == post_id:
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

@app.post("/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(post: PostCreate):
    new_id = max(p["id"] for p in posts) + 1 if posts else 1
    new_post = {
        "id": new_id,
        "author": post.author,
        "title": post.title,
        "content": post.content,
        "date_posted": "2026-01-31"  # In a real app, use the current date
    }
    posts.append(new_post)
    return new_post