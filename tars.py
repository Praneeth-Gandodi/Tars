import logging
import sys

from markrender import MarkdownRenderer

import main
from db import *
from main import *
from styling import input_type, starting
from supporter import *

## To stop the printing of logging in the terminal.
logging.getLogger().setLevel(logging.CRITICAL)
logging.getLogger("RealtimeSTT").setLevel(logging.CRITICAL)
logging.getLogger("faster_whisper").setLevel(logging.CRITICAL)
logging.getLogger("httpx").setLevel(logging.CRITICAL)
logging.getLogger("httpcore").setLevel(logging.CRITICAL)

renderer = MarkdownRenderer(stream_code=False)


def tars():
    audio_reply = False
    starting()

    main.current_session_id = create_new_session(main.model_id)
    opt = input_type()

    if opt == "1":
        func = text_input
    elif opt == "3":
        try:
            with console.status(
                "[green dim]Importing STT module[/green dim]", spinner="dots"
            ) as status:
                from speech_to_text import Audio
        except ImportError as e:
            console.print(f"[red dim]Error: {e}[/red dim]")
        func = Audio
    elif opt == "2":
        try:
            with console.status(
                "[green dim]Importing STT & TTS modules [/green dim]", spinner="dots"
            ) as status:
                from speech_to_text import Audio, initialize_recorder, interrupt_event
                from text_to_speech import tts_pipeline
        except ImportError as e:
            console.print(f"[red dim]Error: {e}[/red dim]")
        func = Audio
        audio_reply = True
        initialize_recorder()  # VAD runs in the background so speech can interrupt TTS
    else:
        console.print("[red]Invalid choice[/red]")
        return

    while True:
        try:
            status = get_ai(func)
        except KeyboardInterrupt:
            console.print(
                "\n[bold yellow]Keyboard intereption detected type '/exit' to quit.[/bold yellow]"
            )
            print()
            continue

        if status == "/exit":
            end_session(main.current_session_id)
            sys.exit(1)

        # Local commands (/help, /sessions, /resume) return "" — nothing to render.
        if not status:
            continue

        try:
            renderer.render(status)
            renderer.finalize()
            if audio_reply:
                tts_pipeline(text=status, interrupt_event=interrupt_event)
        except Exception as e:
            console.print(status)

        # After every response, maybe compact the context (runs every N turns).
        try:
            compacted = main.check_auto_compact()
            if compacted:
                console.print("[green dim]Conversation compacted:[/green dim]")
                console.print(f"[grey93]{compacted}[/grey93]")
        except Exception as e:
            console.print(f"[yellow]Error while compacting the chat: {e}[/yellow]")


if __name__ == "__main__":
    try:
        tars()
    except Exception as e:
        console.print(f"Error occured: {e}")
        end_session(main.current_session_id)
        sys.exit(1)
