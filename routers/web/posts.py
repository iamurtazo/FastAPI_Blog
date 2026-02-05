from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import models
from database import get_db
from schemas import PostResponse


router = APIRouter(
    prefix="/posts",
    tags=["Web"]
)

templates = Jinja2Templates(directory="templates")


@router.get("/{post_id}", response_model=PostResponse, include_in_schema=False, name="post_detail")
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

@router.post("", include_in_schema=False, name="create_post")
async def create_post_page(request: Request):
    return templates.TemplateResponse(
        "create_post.html",
        {
            "request": request
        }
    )
