from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.auth import (
    hash_password,
    verify_password,
    create_session,
    clear_session
)


router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse(
        "register.html",
        {
            "request": request,
            "error": None
        }
    )


@router.post("/register")
def register(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(
        User.email == email.lower().strip()
    ).first()

    if existing_user:
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "error": "Diese E-Mail-Adresse ist bereits registriert."
            },
            status_code=400
        )

    user = User(
        name=name.strip(),
        email=email.lower().strip(),
        password_hash=hash_password(password)
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    response = RedirectResponse(
        url="/",
        status_code=303
    )

    create_session(response, user.id)

    return response


@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "error": None
        }
    )


@router.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.email == email.lower().strip()
    ).first()

    if not user or not verify_password(
        password,
        user.password_hash
    ):
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "E-Mail oder Passwort ist falsch."
            },
            status_code=400
        )

    response = RedirectResponse(
        url="/",
        status_code=303
    )

    create_session(response, user.id)

    return response


@router.post("/logout")
def logout():
    response = RedirectResponse(
        url="/",
        status_code=303
    )

    clear_session(response)

    return response