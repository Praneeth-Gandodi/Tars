from RealtimeSTT import AudioToTextRecorder
from rich.console import Console
console = Console()
conti = True 
recorder = None
def Audio(): 
    global conti
    global recorder
    console.print("[green dim]Speech engine is getting ready.[/green dim]")
    console.print("[green dim]Activating Vocal Processing Unit[/green dim]")
    try:
        if recorder is None:
            recorder = AudioToTextRecorder(
            model='small.en',
            language='en',
            device="cpu", 
            compute_type="float32",
            min_gap_between_recordings= 2.0,
            )
        console.print("[green]\nListening..")
    except Exception as e:
        console.print(f"[/red]Error: Failed to initialize recorder {e}[/red]")
        console.input("[yellow]Falling back to text input.[/yellow]")
        return None
    text = recorder.text()
    print(f"You said: {text}") 
    cleaned_text = text.strip().rstrip('.!?,;:').lower()   
    if cleaned_text in ["q", "quit", "exit", "stop"]: 
        print(f"[red]Shutdown signal received: {text}")
        recorder.shutdown()
        conti = False 
        return "exit"  
    return text

if __name__ == "__main__":
    while conti:
        try:
            Audio()
        except KeyboardInterrupt:
            console.print("\n[bold red]TARS SHUTDOWN SUCCESSFUL[/bold red]", justify="center")

