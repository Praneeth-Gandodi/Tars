from rich.console import Console
from rich.markdown import Markdown
from dotenv import load_dotenv
from main import available_functions
import os

load_dotenv()
model = os.getenv("model")
console = Console()

def starting():
    console.print("[bold cyan] TARS AI ASSISTANT[bold cyan]", justify="center")
    console.print("[green]● System status: Online[/green]")
    console.print(f"[green]● Model: {model}[/green]")
    console.print(f"[green]● Tools Available: {', '.join(available_functions)}[/green]")
    print()
    
def input_type():
    console.print("[i] Select Input Mode:", style="blue", markup=False)
    console.print("[bright_yellow][1] Voice Input (Audio) [/bright_yellow]")
    console.print("[bright_yellow][2] Text Input (Keyboard) [/bright_yellow]")
    opt = console.input("[bright_yellow]Enter choice: [/bright_yellow]: ")
    return opt

