from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import models
from core.security import (
    hash_password, 
    verify_password, 
    create_access_token,
    CurrentUser
)
from config import settings
from database import get_db
from schemas import (
    UserCreate, 
    UserUpdate,     
    UserPublic, 
    UserPrivate, 
    Token, 
    PostResponse
)


router = APIRouter(
    prefix="/api/users",
    tags=["Users"]
)

DB =  Annotated[AsyncSession, Depends(get_db)]

@router.post("", response_model=UserPrivate, status_code=status.HTTP_201_CREATED) 
async def create_user(user: UserCreate, db: DB):
    result = await db.execute(
        select(models.User)
        .where(func.lower(models.User.username) == user.username.lower())
    )

    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with that {user.username} already exists."
        )
    
    result = await db.execute(
        select(models.User)
        .where(func.lower(models.User.email) == user.email.lower())
    )

    existing_email = result.scalars().first()

    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with that {user.email} already exists."
        )
    
    new_user = models.User(
        username=user.username,
        email = user.email.lower(),
        password_hash=hash_password(user.password)
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], 
    db: DB
):
    result = await db.execute(
        select(models.User)
        .where(func.lower(models.User.email) == form_data.username.lower())
    )
    user = result.scalars().first() 

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token  = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")
    
@router.get("/me", response_model=UserPrivate)
async def get_current_user(current_user: CurrentUser):
    return current_user


@router.get("/{user_id}", response_model=UserPublic)
async def get_user(user_id: int, db: DB):
    result = await db.execute(
        select(models.User)
        .where(models.User.id == user_id)
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found."
        )
    return user


@router.get("", response_model=list[UserPublic])
async def get_users(db: DB):
    result = await db.execute(
        select(models.User)
        .order_by(models.User.id.asc())
    )
    users = result.scalars().all()
    return users


@router.get("/{user_id}/posts", response_model=list[PostResponse])
async def get_user_posts(user_id: int, db: DB):
    result = await db.execute(
        select(models.User)
        .where(models.User.id == user_id)
    )
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
    )
    posts = results.scalars().all()
    return posts

@router.patch("/{user_id}", response_model=UserPrivate)
async def update_user(
    user_id: int, 
    current_user: CurrentUser,
    user_update_data: UserUpdate,
    db: DB,
): 
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update this user."
        )
    
    result = await db.execute(
        select(models.User)
        .where(models.User.id == user_id)
    ) 
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found."
        )
    
    if user_update_data.username is not None and user_update_data.username.lower() != user.username.lower():
        result = await db.execute(
            select(models.User)
            .where(func.lower(models.User.username) == user_update_data.username.lower())
        )
        existing_user = result.scalars().first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with that {user_update_data.username} already exists."
            )
    if user_update_data.email is not None and user_update_data.email.lower() != user.email.lower():
        result = await db.execute(
            select(models.User)
            .where(func.lower(models.User.email) == user_update_data.email.lower())
        )
        existing_user = result.scalars().first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with that {user_update_data.email} already exists."
            )
    
    if user_update_data.username is not None: user.username = user_update_data.username.lower()
    if user_update_data.email is not None: user.email = user_update_data.email.lower()
    if user_update_data.image_file is not None: user.image_file = user_update_data.image_file

    await db.commit()
    await db.refresh(user)
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id:int, 
    current_user: CurrentUser,
    db: DB
):
    if user.id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this user."
        )

    result = await db.execute(
        select(models.User)
        .where(models.User.id == user_id)
    )
    user = result.scalars().first() 

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found."
        )
    await db.delete(user)
    await db.commit()



