import os

from itsdangerous import URLSafeSerializer
from passlib.context import CryptContext

from fastapi import Request, HTTPException, Depends
from fastapi.responses import Response

from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User


SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "dev-secret-key"
)

SESSION_COOKIE = "team_app_session"

serializer = URLSafeSerializer(
    SECRET_KEY,
    salt="session"
)

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(
    password: str,
    password_hash: str
):
    return pwd_context.verify(
        password,
        password_hash
    )


def create_session(
    response: Response,
    user_id: int
):
    token = serializer.dumps({
        "user_id": user_id
    })

    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 30
    )


def clear_session(response: Response):
    response.delete_cookie(
        SESSION_COOKIE
    )


def get_current_user(
    request: Request,
    db: Session
):
    token = request.cookies.get(
        SESSION_COOKIE
    )

    if not token:
        return None

    try:
        data = serializer.loads(token)

    except Exception:
        return None

    user_id = data.get("user_id")

    if not user_id:
        return None

    user = db.query(User).filter(
        User.id == user_id
    ).first()

    return user


def login_required(
    request: Request,
    db: Session = Depends(get_db)
):
    user = get_current_user(
        request,
        db
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Login required"
        )

    return user