from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import models
from database import get_db
from schemas import UserCreate, UserResponse, UserUpdate, PostResponse


router = APIRouter(
    prefix="/api/users",
    tags=["Users"]
)

@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED) 
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
    await db.commit()
    await db.refresh(new_user)

    return new_user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_api(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found."
        )
    return user


@router.get("", response_model=list[UserResponse])
async def get_users_api(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.User).order_by(models.User.id.asc())
    )
    users = result.scalars().all()
    return users


@router.get("/{user_id}/posts", response_model=list[PostResponse])
async def get_user_posts_api(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user=result.scalars().first()


    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found." 
        )
    
    results = await db.execute(
        select(models.Post).options(selectinload(models.Post.author)).where(models.Post.user_id == user_id)
    )
    posts = results.scalars().all()
    return posts

@router.patch("/{user_id}", response_model=UserResponse)
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

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
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



