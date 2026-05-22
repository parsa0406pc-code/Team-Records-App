from fastapi import FastAPI, Request, Depends
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session

from app.database import (
    Base,
    engine,
    get_db
)

from app.models import (
    User,
    Record
)

from app.auth import get_current_user

from app.routers import (
    users,
    records
)


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Team Records App"
)

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)

templates = Jinja2Templates(
    directory="templates"
)

app.include_router(users.router)
app.include_router(records.router)


@app.get("/")
def home(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if not user:

        return RedirectResponse(
            url="/login",
            status_code=303
        )

    all_records = db.query(Record).order_by(
        Record.created_at.desc()
    ).all()

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "user": user,
            "records": all_records
        }
    )