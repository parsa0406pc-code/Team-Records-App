from fastapi import FastAPI, Request, Depends
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.database import Base, engine
from app.models import User
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
    user: User = Depends(get_current_user)
):
    if not user:

        return RedirectResponse(
            url="/login",
            status_code=303
        )

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "user": user
        }
    )