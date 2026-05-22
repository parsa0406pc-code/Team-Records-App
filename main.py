from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.database import Base, engine
from app.routers import users


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Team Records App"
)

app.include_router(users.router)

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)

templates = Jinja2Templates(
    directory="templates"
)


@app.get("/")
def home():
    return {
        "message": "Team Records App Running"
    }