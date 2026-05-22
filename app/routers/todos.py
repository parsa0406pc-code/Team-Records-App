from fastapi import (
    APIRouter,
    Form,
    Depends,
    HTTPException
)

from fastapi.responses import RedirectResponse

from sqlalchemy.orm import Session

from app.database import get_db

from app.models import (
    Todo,
    User
)

from app.auth import login_required


router = APIRouter()


@router.post("/todos")
def create_todo(
    task: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(login_required)
):
    todo = Todo(
        task=task,
        created_by=user.id
    )

    db.add(todo)
    db.commit()

    return RedirectResponse(
        url="/",
        status_code=303
    )


@router.post("/todos/{todo_id}/toggle")
def toggle_todo(
    todo_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(login_required)
):
    todo = db.query(Todo).filter(
        Todo.id == todo_id
    ).first()

    if not todo:
        raise HTTPException(
            status_code=404,
            detail="Todo not found"
        )

    todo.done = not todo.done

    db.commit()

    return RedirectResponse(
        url="/",
        status_code=303
    )


@router.post("/todos/{todo_id}/delete")
def delete_todo(
    todo_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(login_required)
):
    todo = db.query(Todo).filter(
        Todo.id == todo_id
    ).first()

    if not todo:
        raise HTTPException(
            status_code=404,
            detail="Todo not found"
        )

    db.delete(todo)
    db.commit()

    return RedirectResponse(
        url="/",
        status_code=303
    )