from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

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


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
@app.get("/posts", response_class=HTMLResponse, include_in_schema=False)
def home():
    return f"<h1>Welcome to the Blog Home Page</h1><p>There are {len(posts)} posts available.</p>"

@app.get("/api/posts")
def get_posts():
    return {
        "posts": posts
    }