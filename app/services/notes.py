from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.note import Note
from app.schemas.notes import NoteCreate


async def list_notes(session: AsyncSession) -> list[Note]:
    result = await session.scalars(select(Note).order_by(Note.id))
    return list(result)


async def create_note(session: AsyncSession, data: NoteCreate) -> Note:
    note = Note(**data.model_dump())
    session.add(note)
    await session.commit()
    return note
