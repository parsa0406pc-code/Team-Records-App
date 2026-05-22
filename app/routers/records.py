from pathlib import Path
import shutil
import uuid

from fastapi import (
    APIRouter,
    Request,
    Form,
    Depends,
    UploadFile,
    File,
    HTTPException
)

from fastapi.responses import RedirectResponse

from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session

from app.database import get_db

from app.models import (
    Record,
    User,
    Attachment
)

from app.auth import login_required


router = APIRouter()

templates = Jinja2Templates(
    directory="templates"
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.get("/records/new")
def new_record_page(
    request: Request,
    user: User = Depends(login_required)
):
    return templates.TemplateResponse(
        request=request,
        name="record_form.html",
        context={
            "user": user
        }
    )


@router.post("/records")
async def create_record(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    files: list[UploadFile] = File(default=[]),
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
    db.refresh(record)

    for uploaded_file in files:

        if not uploaded_file.filename:
            continue

        original_name = uploaded_file.filename

        safe_original_name = original_name.replace(
            "/",
            "_"
        ).replace(
            "\\",
            "_"
        )

        stored_name = f"{uuid.uuid4()}_{safe_original_name}"

        file_path = UPLOAD_DIR / stored_name

        with file_path.open("wb") as buffer:
            shutil.copyfileobj(
                uploaded_file.file,
                buffer
            )

        attachment = Attachment(
            record_id=record.id,
            original_name=safe_original_name,
            stored_name=stored_name,
            content_type=uploaded_file.content_type or "application/octet-stream"
        )

        db.add(attachment)

    db.commit()

    return RedirectResponse(
        url="/",
        status_code=303
    )


@router.get("/records/{record_id}")
def record_detail(
    record_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(login_required)
):
    record = db.query(Record).filter(
        Record.id == record_id
    ).first()

    if not record:
        raise HTTPException(
            status_code=404,
            detail="Record not found"
        )

    return templates.TemplateResponse(
        request=request,
        name="record_detail.html",
        context={
            "user": user,
            "record": record
        }
    )