from rich.console import Console
from dotenv import load_dotenv
from supporter import clear_console, available_functions
from prompt_toolkit.shortcuts import choice
from prompt_toolkit.styles import Style
import os
import sys

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

    console.print(f"[bright_cyan]{TARS_ASCII_LOGO}[/bright_cyan]", justify="left")
    console.print(f"[green]● Model: [aquamarine1]{model}[/aquamarine1][/green]")
    console.print(f"[green]● Tools: [aquamarine1]{len(available_functions)}[/aquamarine1] loaded    Type [bright_cyan]/help[/bright_cyan] to see commands[/green]")
    
def input_type():
    try:
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
    except KeyboardInterrupt as e:
        console.print("[red]Keyboard Interruption detected. Shutting down...[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red] Going to default mode because of: {e}")
        result = "1"
    return result
