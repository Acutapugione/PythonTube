import asyncio
import json
import os
from typing import Optional, Union
from fastapi.responses import HTMLResponse, StreamingResponse
from typing_extensions import Annotated
from fastapi import (
    Depends,
    FastAPI,
    BackgroundTasks,
    Header,
    Response,
    UploadFile,
    File,
)
from sqlmodel import (
    SQLModel,
    Field,
    Session,
    create_engine,
    Relationship,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import yt_dlp

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from pydantic import HttpUrl


DATABASE_URL = "sqlite:///my_db.db"
app = FastAPI(description="мікросервіс FastAPI для завантаження(uploading) відео")
# engine = create_async_engine("sqlite:///my_db.db", echo=True)
# SessionMaker = async_sessionmaker(bind=engine, expire_on_commit=False)
# engine = create_engine(DATABASE_URL, echo=True)
engine = create_engine(DATABASE_URL, echo=True)
session_local = sessionmaker(
    bind=engine,
    autoflush=True,
    # expire_on_commit=False,
)


class TagVideoLink(SQLModel, table=True):
    tag_id: int | None = Field(
        default=None,
        foreign_key="tag.id",
        primary_key=True,
    )
    video_base_id: int | None = Field(
        default=None,
        foreign_key="videobase.id",
        primary_key=True,
    )


class CategoryVideoLink(SQLModel, table=True):
    category_id: int | None = Field(
        default=None,
        foreign_key="category.id",
        primary_key=True,
    )
    video_base_id: int | None = Field(
        default=None,
        foreign_key="videobase.id",
        primary_key=True,
    )


class Category(SQLModel, table=True):
    id: int | None = Field(
        default=None,
        primary_key=True,
    )
    name: str = Field(unique=True)
    videos: list["VideoBase"] = Relationship(
        back_populates="categories",
        link_model=CategoryVideoLink,
    )


class Tag(SQLModel, table=True):
    id: int | None = Field(
        default=None,
        primary_key=True,
    )

    videos: list["VideoBase"] = Relationship(
        back_populates="tags",
        link_model=TagVideoLink,
    )
    name: str = Field(unique=True)


class VideoBase(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    title: str = Field(unique=True)
    categories: list["Category"] = Relationship(
        back_populates="videos",
        link_model=CategoryVideoLink,
    )
    tags: list["Tag"] = Relationship(
        back_populates="videos",
        link_model=TagVideoLink,
    )
    description: str
    path: str


class Video(SQLModel):
    url: HttpUrl  # https://www.youtube.com/watch?v=53SyywtK0XU


def download_youtube_video(url, output_path):
    ydl_opts = {
        "outtmpl": f"{output_path}/%(title)s.%(ext)s",
        "format": "best",
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url)
        return info


def fetch_entities(
    entity_type: type, session
):  # , items: list[Union[Category, Tag, VideoBase]]):
    return session.scalars(select(entity_type)).all()


async def create_video(video: Video):
    url = str(video.url)

    # 1 Завантажити відео з ютуб в downloads/
    info = download_youtube_video(url=url, output_path="./downloads")
    if not info:
        return

    title = info.get("title", "")
    description = info.get("description", "")
    categories = info.get("categories", [])
    tags = info.get("tags", [])
    ext = info.get("ext")
    # 2 Додати в базу даних Video з адресою
    path = os.path.join("downloads", f"{title}.{ext}")

    with session_local.begin() as session:
        existing_videos = [item.title for item in fetch_entities(VideoBase, session)]
        if title in existing_videos:
            return
        video_item = VideoBase(
            description=description,
            title=title,
            path=path,
        )
        existing_categories = [item.name for item in fetch_entities(Category, session)]
        non_existing_categories = [
            title for title in categories if title not in existing_categories
        ]
        video_item.categories.extend(existing_categories)
        video_item.categories.extend(
            [Category(name=category) for category in non_existing_categories]
        )
        # session.bulk_insert_mappings(
        #     Category,
        #     [{"name": cat, "videos": [video_item]} for cat in non_existing_categories],
        # )
        existing_tags = [item.name for item in fetch_entities(Tag, session)]
        non_existing_tags = [title for title in tags if title not in existing_tags]
        video_item.tags.extend(existing_tags)
        video_item.tags.extend([Tag(name=tag) for tag in non_existing_tags])
        session.add(video_item)


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(
        open("templates/player.html").read(),
        status_code=200,
    )


@app.get("/video")
async def video_endpoint(video_path: str):
    def iterfile():
        with open(video_path, mode="rb") as file_like:
            yield from file_like

    return StreamingResponse(iterfile(), media_type="video/mp4")


@app.post("/video")
async def add_video(video: Annotated[Video, Depends()], bg_tasks: BackgroundTasks):
    bg_tasks.add_task(create_video, video=video)
    return {"msg": "Done"}


SQLModel.metadata.drop_all(engine)
SQLModel.metadata.create_all(engine)
