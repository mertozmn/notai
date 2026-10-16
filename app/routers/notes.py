from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Note, User
from app.schemas import NoteCreate, NoteOut

router = APIRouter(prefix="/notes", tags=["notes"])


def get_own_note(note_id: int, user: User, db: Session) -> Note:
    note = db.scalar(select(Note).where(Note.id == note_id, Note.user_id == user.id))
    if note is None:
        raise HTTPException(status_code=404, detail="Not bulunamadı")
    return note


@router.post("", status_code=201, response_model=NoteOut)
def create_note(
    data: NoteCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    note = Note(user_id=user.id, title=data.title, content=data.content)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.get("", response_model=list[NoteOut])
def list_notes(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = (
        select(Note)
        .where(Note.user_id == user.id)
        .order_by(Note.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return db.scalars(stmt).all()


@router.get("/{note_id}", response_model=NoteOut)
def get_note(
    note_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_own_note(note_id, user, db)


@router.put("/{note_id}", response_model=NoteOut)
def update_note(
    note_id: int,
    data: NoteCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    note = get_own_note(note_id, user, db)
    note.title = data.title
    note.content = data.content
    db.commit()
    db.refresh(note)
    return note


@router.delete("/{note_id}", status_code=204)
def delete_note(
    note_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    note = get_own_note(note_id, user, db)
    db.delete(note)
    db.commit()