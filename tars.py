from main import get_ai, console, ccount, summarize, text_input
from styling import starting, input_type
from rich.markdown import Markdown
from stt import Audio
import logging


logging.getLogger().setLevel(logging.CRITICAL)
logging.getLogger("RealtimeSTT").setLevel(logging.CRITICAL)
logging.getLogger("faster_whisper").setLevel(logging.CRITICAL)
logging.getLogger("httpx").setLevel(logging.CRITICAL)
logging.getLogger("httpcore").setLevel(logging.CRITICAL)

def tars():
    global ccount
    starting()
    opt = input_type()
    if opt == "1":
        func = Audio
    elif opt == "2":
        func = text_input
    else:
        console.print("[red]Invalid choice[/red]")
        return
    while True:
        status = get_ai(func)
        if status in ["q", "quit", "exit", "stop"]:
            return 
        if status.lower() == "summarize":
            console.print(summarize())
        md = Markdown(status)
        console.print(md)
        ccount += 1
        console.print(f"[deep_sky_blue1 dim]{ccount}[/deep_sky_blue1 dim]", justify="right")
        if ccount % 10 == 0:  # every 10 chats
            yn = console.input("Summarize the chat to save tokens? [Yes/No]: ").strip().lower()
            if yn in ["yes", "y", "yes."]:
                console.print("Summarized chat:")
                console.print(summarize()) 
            else:
                console.print("Skipping summarization for now.")

        
if __name__ == "__main__":
    try:
        tars()
    except KeyboardInterrupt:
        console.print("\n[bold red]TARS SHUTDOWN SUCCESSFUL[/bold red]", justify="center")
