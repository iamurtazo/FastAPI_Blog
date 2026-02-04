from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter(
    include_in_schema=False,
    tags=["Web Auth"]
)

templates = Jinja2Templates(directory="templates")


@router.get("/login", name="login")
async def login_page(request: Request):
    """Display login page"""
    return templates.TemplateResponse(
        request,
        "login.html",
        {"title": "Login"},
    )


@router.get("/register", name="register")
async def register_page(request: Request):
    """Display registration page"""
    return templates.TemplateResponse(
        request,
        "register.html",
        {"title": "Register"},
    )