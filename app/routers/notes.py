from fastapi import APIRouter, status

from app.core.deps import SessionDep
from app.schemas.notes import NoteCreate, NoteRead
from app.services import notes

router = APIRouter(prefix="/notes", tags=["notes"])


@router.get("")
async def list_notes(session: SessionDep) -> list[NoteRead]:
    return [NoteRead.model_validate(note) for note in await notes.list_notes(session)]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_note(data: NoteCreate, session: SessionDep) -> NoteRead:
    return NoteRead.model_validate(await notes.create_note(session, data))
