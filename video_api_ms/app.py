import asyncio
from typing import Optional
from fastapi.responses import HTMLResponse, StreamingResponse
from typing_extensions import Annotated
from fastapi import Depends, FastAPI, BackgroundTasks, Response, UploadFile, File
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
    # category: str  # категорія або тег
    url: str  # | str

    # file: str


class Video(SQLModel):
    # name: str
    # description: str
    # category: str  # категорія або тег
    url: HttpUrl
    # file: UploadFile


async def create_video(video: Video):
    url = str(video.url)
    # with SessionMaker() as session:
    #     name, description = await download_yt_video(url)
    #     session.add(VideoBase(name=name, description=description, url=url))
    #     session.commit()


# async def download_yt_video(url: str):
#     with YoutubeDL(
#         {}
#     ) as downloader:
#         downloader.download(
#             [
#                 url,
#             ]
#         )
# video = YouTube(
#     url,
#     use_oauth=False,
#     allow_oauth_cache=True,
# )

# print(
#     f"{video.streams=}"  # .filter(file_extension='mp4', res="720p").first().download()=}"
# )

# stream = video.streams.first()

# if stream:
#     stream.download("media")
# return video.title, video.description


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(
        open("templates/player.html").read(),
        status_code=200,
    )


@app.get("/video")
async def video_endpoint(video_path):
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


# async def main():
#     await download_yt_video("https://youtu.be/J-LxmSdxYRI?si=Xr5WDe-laq83zgjW")


# asyncio.run(main())
