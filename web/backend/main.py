from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select

import uuid
from pathlib import Path
from datetime import datetime


def find_project_root(marker=".git"):
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / marker).exists():
            return parent
    return current.parent


project_root = find_project_root()
db_path = project_root / "database.db"


class ChatMessage(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(index=True)
    timestamp: datetime = Field(index=True)
    channel_name: str = Field(index=True)
    username: str | None = Field(default=None, index=True)
    message_text: str
    message_type: str


sqlite_url = f"sqlite:///{db_path}"
engine = create_engine(sqlite_url)

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, echo=True, connect_args=connect_args)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]

app = FastAPI()


@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/chats/")
def get_chats(
    session: SessionDep,
    channel_name: Annotated[str, Query(title="Channel name")] = None,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[ChatMessage]:

    if channel_name is None:
        stmt = select(ChatMessage).offset(offset).limit(limit)
    else:
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.channel_name == channel_name)
            .offset(offset)
            .limit(limit)
        )
    results = session.exec(stmt).all()
    return results
