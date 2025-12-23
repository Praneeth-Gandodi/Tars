import os
import subprocess
from tools.weather import get_weather
from tools.DateTime import *
from tools.news import get_news
from tools.wiki import *
from tools.websearch import *
from tools.video_download import * 
from tools.file_handler import *
from tools.sptest import sptest

def clear_console():
    command = "cls" if os.name == "nt" else "clear"
    subprocess.run(command, shell=True)
    return "The screen has been cleard"

available_functions = {
    "get_weather": get_weather, 
    "get_datetime": get_datetime,
    "get_dt_by_place":get_dt_by_place,
    "get_news": get_news,
    "wiki_search": wiki_search,
    "wiki_summary": wiki_summary,
    "wiki_content": wiki_content,
    "web_search":web_search,
    "image_search":image_search,
    "video_search":video_search,
    "news_search": news_search,
    "yt_info": yt_info,
    "yt_videoDownload": yt_videoDownload,
    "yt_AudioDownload" : yt_AudioDownload,
    "ig_download": ig_download,
    "fb_download": fb_download,
    "list_files_in_directory":list_files_in_directory,
    "list_files_by_types":list_files_by_types,
    "read_file_content":read_file_content,
    "write_to_files":write_to_files,
    "write_docx":write_docx,
    "recursive_file_search":recursive_file_search,
    "open_file":open_file,   
    "clear_console":clear_console,
    "sptest": sptest
}

