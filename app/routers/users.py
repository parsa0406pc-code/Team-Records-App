import re
import secrets

from datetime import datetime, timedelta

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
    clear_session,
    login_required
)

from app.email_utils import send_email


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

    if not user or not verify_password(password, user.password_hash):
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


@router.get("/forgot-password")
def forgot_password_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="forgot_password.html",
        context={
            "user": None,
            "error": None,
            "success": None
        }
    )


@router.post("/forgot-password")
def forgot_password(
    request: Request,
    email: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.email == email.lower().strip()
    ).first()

    success_message = "Falls diese E-Mail existiert, wurde ein Link zum Zurücksetzen gesendet."

    if not user:
        return templates.TemplateResponse(
            request=request,
            name="forgot_password.html",
            context={
                "user": None,
                "error": None,
                "success": success_message
            }
        )

    token = secrets.token_urlsafe(32)

    user.password_reset_token = token
    user.password_reset_expires_at = datetime.utcnow() + timedelta(minutes=30)

    db.commit()

    reset_link = str(request.url_for(
        "reset_password_page",
        token=token
    ))

    send_email(
        to_email=user.email,
        subject="Passwort zurücksetzen",
        body=f"""
Hallo {user.name},

du kannst dein Passwort über diesen Link zurücksetzen:

{reset_link}

Der Link ist 30 Minuten gültig.

Team Records
"""
    )

    return templates.TemplateResponse(
        request=request,
        name="forgot_password.html",
        context={
            "user": None,
            "error": None,
            "success": success_message
        }
    )


@router.get("/reset-password/{token}")
def reset_password_page(
    token: str,
    request: Request,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.password_reset_token == token
    ).first()

    if not user or not user.password_reset_expires_at:
        return templates.TemplateResponse(
            request=request,
            name="reset_password.html",
            context={
                "user": None,
                "token": token,
                "error": "Dieser Link ist ungültig.",
                "success": None
            },
            status_code=400
        )

    if user.password_reset_expires_at < datetime.utcnow():
        return templates.TemplateResponse(
            request=request,
            name="reset_password.html",
            context={
                "user": None,
                "token": token,
                "error": "Dieser Link ist abgelaufen.",
                "success": None
            },
            status_code=400
        )

    return templates.TemplateResponse(
        request=request,
        name="reset_password.html",
        context={
            "user": None,
            "token": token,
            "error": None,
            "success": None
        }
    )


@router.post("/reset-password/{token}")
def reset_password(
    token: str,
    request: Request,
    new_password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.password_reset_token == token
    ).first()

    if not user or not user.password_reset_expires_at:
        return templates.TemplateResponse(
            request=request,
            name="reset_password.html",
            context={
                "user": None,
                "token": token,
                "error": "Dieser Link ist ungültig.",
                "success": None
            },
            status_code=400
        )

    if user.password_reset_expires_at < datetime.utcnow():
        return templates.TemplateResponse(
            request=request,
            name="reset_password.html",
            context={
                "user": None,
                "token": token,
                "error": "Dieser Link ist abgelaufen.",
                "success": None
            },
            status_code=400
        )

    password_is_valid, password_error = is_strong_password(new_password)

    if not password_is_valid:
        return templates.TemplateResponse(
            request=request,
            name="reset_password.html",
            context={
                "user": None,
                "token": token,
                "error": password_error,
                "success": None
            },
            status_code=400
        )

    user.password_hash = hash_password(new_password)
    user.password_reset_token = None
    user.password_reset_expires_at = None

    db.commit()

    return templates.TemplateResponse(
        request=request,
        name="reset_password.html",
        context={
            "user": None,
            "token": token,
            "error": None,
            "success": "Passwort wurde erfolgreich geändert. Du kannst dich jetzt anmelden."
        }
    )


@router.get("/profile")
def profile_page(
    request: Request,
    user: User = Depends(login_required)
):
    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={
            "user": user,
            "error": None,
            "success": None
        }
    )


@router.post("/profile/update-name")
def update_name(
    request: Request,
    name: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(login_required)
):
    user.name = name.strip()

    db.commit()
    db.refresh(user)

    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={
            "user": user,
            "error": None,
            "success": "Name wurde erfolgreich geändert."
        }
    )


@router.post("/profile/update-password")
def update_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(login_required)
):
    if not verify_password(current_password, user.password_hash):
        return templates.TemplateResponse(
            request=request,
            name="profile.html",
            context={
                "user": user,
                "error": "Das aktuelle Passwort ist falsch.",
                "success": None
            },
            status_code=400
        )

    password_is_valid, password_error = is_strong_password(new_password)

    if not password_is_valid:
        return templates.TemplateResponse(
            request=request,
            name="profile.html",
            context={
                "user": user,
                "error": password_error,
                "success": None
            },
            status_code=400
        )

    user.password_hash = hash_password(new_password)

    db.commit()

    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={
            "user": user,
            "error": None,
            "success": "Passwort wurde erfolgreich geändert."
        }
    )


@router.post("/profile/delete")
def delete_account(
    current_password: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(login_required)
):
    if not verify_password(current_password, user.password_hash):
        return RedirectResponse(
            url="/profile",
            status_code=303
        )

    response = RedirectResponse(
        url="/register",
        status_code=303
    )

    clear_session(response)

    db.delete(user)
    db.commit()

    return response