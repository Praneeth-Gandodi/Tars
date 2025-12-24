from RealtimeSTT import AudioToTextRecorder
from rich.console import Console
from rich.live import Live
from rich.text import Text
import sys
import logging


logging.getLogger("RealtimeSTT").setLevel(logging.CRITICAL)
logging.getLogger("realtimestt").setLevel(logging.CRITICAL)
logging.getLogger("faster_whisper").setLevel(logging.CRITICAL)
logging.getLogger("silero").setLevel(logging.CRITICAL)
logging.getLogger("webrtcvad").setLevel(logging.CRITICAL)

console = Console()
recorder = None
live_display = None

def initialize_recorder():
    """Initialize the recorder once"""
    global recorder
    
    if recorder is None:
        try:
            recorder = AudioToTextRecorder(
                model='small.en',
                language='en',
                device="cpu", 
                compute_type="float32",
                post_speech_silence_duration=2.0,
                silero_sensitivity=0.5,
                enable_realtime_transcription=True,
                on_realtime_transcription_update=on_partial,
                on_recording_start=lambda: None,
                spinner=False,
                level=logging.CRITICAL, 
            )
        except Exception as e:
            console.print(f"[red]Error initializing recorder: {e}[/red]")
            return False
    return True

def on_partial(text):
    """Update the live display with partial transcription"""
    global live_display
    if live_display and text:
        live_display.update(Text(f"{text}", style="green dim"))

def Audio():
    """Capture a single voice input and return the text"""
    global recorder, live_display

    if not initialize_recorder():
        return None
    
    try:
        with Live(Text("Speak Now", style="cyan dim"), console=console, refresh_per_second=10) as live:
            live_display = live
            

            full_text = recorder.text()
            
            live_display = None  
        
        if full_text:
            cleaned = full_text.strip().rstrip('.!?,;:').lower()
            if cleaned in ["q", "quit", "exit", "stop"]:
                console.print("[red]Shutdown signal received[/red]")
                shutdown_recorder()
                return cleaned
            
            console.print(f"[green]You said:[/green] {full_text}")
            return full_text
        else:
            return ""
            
    except Exception as e:
        console.print(f"\n[red]Error during recording: {e}[/red]")
        live_display = None
        return None

def shutdown_recorder():
    """Shutdown the recorder"""
    global recorder
    if recorder:
        try:
            recorder.shutdown()
            console.print("[yellow]Voice input shutdown[/yellow]")
        except:
            pass
        recorder = None

if __name__ == "__main__":
    try:
        initialize_recorder()
        while True:
            text = Audio()
            if text and text.lower() in ["q", "quit", "exit", "stop"]:
                break
    except KeyboardInterrupt:
        console.print("\n[bold red]TARS SHUTDOWN SUCCESSFUL[/bold red]", justify="center")
        shutdown_recorder()