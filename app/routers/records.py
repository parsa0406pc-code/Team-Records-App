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

from app.models import (
    Record,
    User
)

from app.auth import (
    login_required
)


router = APIRouter()

templates = Jinja2Templates(
    directory="templates"
)


@router.get("/records/new")
def new_record_page(
    request: Request,
    user: User = Depends(login_required)
):
    return templates.TemplateResponse(
        request=request,
        name="record_form.html"
    )


@router.post("/records")
def create_record(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(login_required)
):
    record = Record(
        title=title,
        description=description,
        creator_id=user.id
    )

    db.add(record)

    db.commit()

    return RedirectResponse(
        url="/",
        status_code=303
    )