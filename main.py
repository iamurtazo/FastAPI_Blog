from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

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
    # return templates.TemplateResponse("home.html", {"request": request, "posts": posts})
    return templates.TemplateResponse(
        request, 
        'home.html', 
        {
            "request": request, 
            "posts": posts
        }
    )
# post detail api
@app.get("/posts/{post_id}", include_in_schema=False)
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
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "error_title": "Post Not Found",
            "error_message": f"Sorry, the post with ID {post_id} does not exist.",
            "home_link": "/posts"
        }
    )


@app.get("/posts")
def get_posts(): 
    return {
        "posts": posts
    }