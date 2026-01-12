import yt_dlp 
from pathlib import Path


loc = Path.home()

def yt_info(url):
    """
    Fetches the basic info about the Youtube/Instagram/Facebook/reddit's video from the pasted link.   
    Args:
        url (str): Video URL.
    Returns:
        dict : Title, uploader, duration, view count, thumbnail, format info.
    """
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        best_video = None
        if "formats" in info:
            videos = [f for f in info["formats"] if f.get("vcodec") != "none"]
            if videos:
                best_video = max(videos, key=lambda f: f.get("height") or 0)

        return {
            "title": info.get("title"),
            "channel": info.get("uploader"),
            "duration": info.get("duration"),
            "views": info.get("view_count"),
            "thumbnail": info.get("thumbnail"),
            "resolution": best_video.get("height") if best_video else None,
            "fps": best_video.get("fps") if best_video else None,
            "video_format": best_video.get("ext") if best_video else None,
            "video_note": best_video.get("format_note") if best_video else None,
        }
     
    
def media_downloader(link:str, download_path:str , media_type:str):
    """
        Downlaods audio or video from the passed link and saves it in the given path.
    Args:
        link (str): Link to the video/audio that you want to Downlaod.
        download_path (str): File Downlaod path default will be Downloads folder.
        media_type (str): Type to download Audio or Video.
    Returns:
        str : Download is successful or not.
    """
    home_directory = Path.home()
    download_path = home_directory / download_path   
    yt_opts = {
        "outtmpl": f"{download_path}/%(title)s.%(ext)s",
        'quiet': True,
        'noplaylist': True,
        'progress': True,
        "no_warnings": True,
    }
    media_type = media_type.lower()

    if media_type == "video":
        yt_opts.update({
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "merge_output_format": "mp4",
        })

    elif media_type == "audio":
        yt_opts.update({
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
        })
    else:
        return "Invalid media_type. Use 'audio' or 'video'."
    try:
        with yt_dlp.YoutubeDL(yt_opts) as ydl:
            info = ydl.extract_info(link, download=False)
            title = info.get('title')
            ydl.download([link])
    except Exception as e:
        return f"An ERROR occured while downloading the video : {e}"
    else:    
        return f"Downloaded video '{title}' to location '{download_path}' successfully."