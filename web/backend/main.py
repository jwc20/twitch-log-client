from contextlib import asynccontextmanager
from typing import Annotated

from starlette.middleware.cors import CORSMiddleware
import httpx
from starlette.middleware import Middleware

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select

import uuid
from pathlib import Path
from datetime import datetime


##############################################################################


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


##############################################################################


sqlite_url = f"sqlite:///{db_path}"
engine = create_engine(sqlite_url)

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, echo=True, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]

##############################################################################


def add_cors_middleware(app):
    return CORSMiddleware(
        app=app,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )


def add_logging_middleware(app):
    async def middleware(scope, receive, send):
        path = scope["path"]
        print("Request:", path)
        await app(scope, receive, send)

    return middleware


##############################################################################


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield
    print("shutting down")


app = FastAPI(lifespan=lifespan)
app.add_middleware(add_cors_middleware)
app.add_middleware(add_logging_middleware)


##############################################################################


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
