import os
import subprocess
from rich.console import Console
from tools.weather import get_weather
from tools.DateTime import *
from tools.news import get_news
from tools.wiki import *
from tools.websearch import *
from tools.video_download import * 
from tools.file_handler import *
from tools.sptest import sptest
from tools.memory import *
from tools.app_open import software_opener
from tools.web_browser import open_browser
from tools.browser_control import (
    browser_navigate,
    browser_extract,
    browser_search,
    browser_click,
    browser_fill,
    browser_screenshot,
    browser_close,
)
from tools.system_info import system_info

console = Console()

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
    "media_downloader": media_downloader,
    "list_files_in_directory":list_files_in_directory,
    "list_files_by_types":list_files_by_types,
    "read_file_content":read_file_content,
    "write_to_files":write_to_files,
    "write_docx":write_docx,
    "recursive_file_search":recursive_file_search,
    "open_file":open_file,   
    "clear_console":clear_console,
    "sptest": sptest,
    "manage_memory":manage_memory,
    "software_opener": software_opener,
    "open_browser": open_browser,
    "browser_navigate": browser_navigate,
    "browser_extract": browser_extract,
    "browser_search": browser_search,
    "browser_click": browser_click,
    "browser_fill": browser_fill,
    "browser_screenshot": browser_screenshot,
    "browser_close": browser_close,
    "system_info": system_info,
}

def tars_settings():
    console.print("Settings")
    return 
