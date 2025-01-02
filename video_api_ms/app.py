from token import OP
from typing import Optional
from typing_extensions import Annotated
from fastapi import Depends, FastAPI, BackgroundTasks, UploadFile, File
from sqlmodel import SQLModel, Field, Session, create_engine
from sqlalchemy.orm import sessionmaker

# from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from pydantic import HttpUrl

app = FastAPI(description="мікросервіс FastAPI для завантаження(uploading) відео")
# engine = create_async_engine("sqlite:///my_db.db", echo=True)
# SessionMaker = async_sessionmaker(bind=engine, expire_on_commit=False)
engine = create_engine("sqlite:///my_db.db", echo=True)
SessionMaker = sessionmaker(bind=engine, expire_on_commit=False)


class VideoBase(SQLModel, table=True):
    id: int = Field(primary_key=True, nullable=True, default=None)
    name: str
    description: str
    category: str  # категорія або тег
    file: str


class Video(SQLModel):
    name: str
    description: str
    category: str  # категорія або тег
    url: HttpUrl | str
    file: UploadFile


async def create_video(video: Video):
    with SessionMaker() as session:
        session.add(VideoBase.model_validate(video))
        session.commit()


@app.post("/video")
async def add_video(video: Annotated[Video, Depends()], bg_tasks: BackgroundTasks):
    bg_tasks.add_task(create_video, video=video)
    return {"msg": "Done"}


SQLModel.metadata.drop_all(engine)
SQLModel.metadata.create_all(engine)
