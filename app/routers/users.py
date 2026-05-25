import re

from fastapi import (
    APIRouter,
    Request,
    Form,
    Depends
)

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

templates = Jinja2Templates(
    directory="templates"
)


def is_strong_password(password: str):
    if len(password) < 8:
        return False, "Das Passwort muss mindestens 8 Zeichen lang sein."

    if not re.search(r"[A-Za-z]", password):
        return False, "Das Passwort muss mindestens einen Buchstaben enthalten."

    if not re.search(r"\d", password):
        return False, "Das Passwort muss mindestens eine Zahl enthalten."

    return True, None


@router.get("/register")
def register_page(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={
            "error": None,
            "user": None
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
    password_is_valid, password_error = is_strong_password(password)

    if not password_is_valid:

        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "error": password_error,
                "user": None
            },
            status_code=400
        )

    existing_user = db.query(User).filter(
        User.email == email.lower().strip()
    ).first()

    if existing_user:

        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "error": "Diese E-Mail-Adresse ist bereits registriert.",
                "user": None
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

    create_session(
        response,
        user.id
    )

    return response


@router.get("/login")
def login_page(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "error": None,
            "user": None
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
            request=request,
            name="login.html",
            context={
                "error": "E-Mail oder Passwort ist falsch.",
                "user": None
            },
            status_code=400
        )

    response = RedirectResponse(
        url="/",
        status_code=303
    )

    create_session(
        response,
        user.id
    )

    return response


@router.post("/logout")
def logout():

    response = RedirectResponse(
        url="/",
        status_code=303
    )

    clear_session(response)

    return response