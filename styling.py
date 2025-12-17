from rich.console import Console
from rich.markdown import Markdown
from dotenv import load_dotenv
from supporter import clear_console
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
    console.print("[bright_yellow][1] Voice Interface[/bright_yellow]")
    console.print("[bright_yellow][2] Text Interface[/bright_yellow]")
    opt = console.input("[bright_yellow]❯ Select Interce (1/2)[/bright_yellow]: ")
    return opt if opt in ["1", "2"] else "2"

