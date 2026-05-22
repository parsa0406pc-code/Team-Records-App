from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.database import Base, engine


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


@app.get("/")
def home():
    return {
        "message": "Team Records App Running"
    }