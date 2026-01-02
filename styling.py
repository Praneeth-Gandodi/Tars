from rich.console import Console
from rich.markdown import Markdown
from dotenv import load_dotenv
from supporter import clear_console
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.filters import is_done
from prompt_toolkit.shortcuts import choice
from prompt_toolkit.styles import Style
import os

load_dotenv()
model = os.getenv("model")
console = Console()

def starting():
    clear_console()
    console.print()
    TARS_ASCII_LOGO = """
████████╗ █████╗ ██████╗ ███████╗     ██████╗██╗     ██╗
╚══██╔══╝██╔══██╗██╔══██╗██╔════╝    ██╔════╝██║     ██║
   ██║   ███████║██████╔╝███████╗    ██║     ██║     ██║
   ██║   ██╔══██║██╔══██╗╚════██║    ██║     ██║     ██║
   ██║   ██║  ██║██║  ██║███████║    ╚██████╗███████╗██║
   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝     ╚═════╝╚══════╝╚═╝
"""

    console.print(f"[light_goldenrod2]{TARS_ASCII_LOGO}[/light_goldenrod2]", justify="left")
    console.print(f"[green]● Model: {model}[/green]")
    
def input_type():
    style = Style.from_dict(
        {
            "input-selection":"#D891E8",
            "number":"fg:#1ac3d6 bold",
        }
    )
    result = choice(
        message="Select a Mode:",
        options=[
            ("1", "Text → Text"),
            ("2", "Voice → Voice (STT + TTS)"),
            ("3", "Voice → Text")
        ],
        style=style,
        default="1",
        mouse_support=True,
    )
    return result
