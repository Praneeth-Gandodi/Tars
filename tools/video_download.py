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
     
    
def yt_videoDownload(link , location = "Downloads"):
    """
    Downloads the Youtube video with the best quitlity available.
    Args:
        link (str): Youtube URL to the video.
        location (str, optional): Subfolder under the home directory where the video is downloaded. Defaults to "Downloads".

    Returns:
        str : A string metioning the video download status (Successfull/Failed). If successfull retuns video title and the location where the video downlaoded.
    """
    download_location = loc / location
    ydl_opts = {
        'outtmpl': f'{download_location}/%(title)s.%(ext)s',
        'quiet': True,
        'noplaylist': True,
        'progress': True,
        "no_warnings": True,
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'merge_output_format': 'mp4',
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=False)
            title = info.get('title')
            ydl.download([link])
    except Exception as e:
        return f"An ERROR occured while downloading the video : {e}"
    else:    
        return f"Downloaded video '{title}' to location '{download_location}' successfully."
    
def yt_AudioDownload(link, location="Downloads"):
    """
    Downloads the Youtube Audio with the best quitlity available.
    Args:
        link (str): Youtube URL to the Audio.
        location (str, optional): Subfolder under the home directory where the video is downloaded. Defaults to "Downloads".

    Returns:
        str : A string metioning the video download status (Successfull/Failed). If successfull retuns Audio title and the location where the audio downlaoded.
    """
    download_location = loc / location
    ydl_opts = {
    'outtmpl': f'{download_location}/%(title)s.%(ext)s',
    'quiet': True,
    'noplaylist': True,
    'progress': True,
    "no_warnings": True,
    "format": "bestaudio/best",
    'postprocessors': [
        {
        'key': 'FFmpegVideoConvertor',
        'preferedformat': 'mp3'
        }
        ],
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=False)
            title = info.get('title')
            ydl.download([link])
    except Exception as e:
        return f"An Error occured {e}"
    else:
        return f"Downloaded Audio '{title}' to location '{download_location}' successfully."
    

def ig_download(link, location="Downloads"):
    """
    Downloads the Instagram video with the best quitlity available.
    Args:
        link (str): Instagram URL to the video.
        location (str, optional): Subfolder under the home directory where the video is downloaded. Defaults to "Downloads".

    Returns:
        str : A string metioning the video download status (Successfull/Failed). If successfull retuns video title and the location where the video downlaoded.
    """
    download_location = loc / location
    yt_opts = {
        "outtmpl": f"{download_location}/%(title)s.%(ext)s",
        'quiet': True,
        'noplaylist': True,
        'progress': True,
        "no_warnings": True,
    }
    try:
        with yt_dlp.YoutubeDL(yt_opts) as ydl:
            info = ydl.extract_info(link, download=False)
            title = info.get('title')
            ydl.download([link])
    except Exception as e:
        return f"An Error occured {e}"
    else:
        return f"Downloaded Instagram video '{title}' to location '{download_location}' successfully."
        
def fb_download(link, location="Downloads"):
    """
    Downloads the Facebook video with the best quitlity available.
    Args:
        link (str): Facebook URL to the video.
        location (str, optional): Subfolder under the home directory where the video is downloaded. Defaults to "Downloads".

    Returns:
        str : A string metioning the video download status (Successfull/Failed). If successfull retuns video title and the location where the video downlaoded.
    """    
    download_location = loc / location
    yt_opts = {
        "outtmpl": f"{download_location}/%(title)s.%(ext)s",
        'quiet': True,
        'noplaylist': True,
        'progress': True,
        "no_warnings": True,
    }
    try:
        with yt_dlp.YoutubeDL(yt_opts) as ydl:
            info = ydl.extract_info(link, download=False)
            title = info.get('title')
            ydl.download([link])
    except Exception as e:
        return f"An Error occured {e}"
    else:
        return f"Downloaded Instagram video '{title}' to location '{download_location}' successfully."
        

