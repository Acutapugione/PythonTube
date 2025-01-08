import yt_dlp


def download_youtube_video(url, output_path):
    ydl_opts = {
        "outtmpl": f"{output_path}/%(title)s.%(ext)s",
        "format": "best",
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


# Example usage
download_youtube_video("https://www.youtube.com/watch?v=53SyywtK0XU", "./downloads")
# download_youtube_video("https://www.youtube.com/watch?v=YP6qdfUlIKc", "./downloads")
