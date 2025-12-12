from main import get_ai, console, ccount, summarize, text_input
from styling import starting, input_type
from rich.markdown import Markdown
from stt import Audio
from db import get_last_messages
import logging
import sys



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
        if status == None:
            func = text_input
        if status in ["q", "quit", "exit", "stop"]:
            return 
        if status.lower() == "summarize":
            try:
                last_10_messages = get_last_messages(limit=10)
            except Exception as e:
                console.print(f"[red] No messages to summarize[/red]")
                continue
            else:
                summary_prompt = "Summarize these messages concisely:\n"
                
                for msg in last_10_messages:
                    summary_prompt += f"{msg['role']}:{msg['content']}\n"

                # Call summarize using the prompt
                summary_text = summarize(custom_prompt=summary_prompt)
                console.print("Summarized chat:")
                console.print(f"[grey93]{summary_text}[/grey93]") 
            
        console.print("[bold green]>> TARS:[/bold green]", end=" ")

        try:
            md = Markdown(status)
            console.print(md)
        except Exception as e:
            console.print(status)
                    
        ccount += 1
        console.print(f"[deep_sky_blue1 dim]{ccount}[/deep_sky_blue1 dim]", justify="right")
        
        ## summarizin for every ten messages to reduce the usage of tokens.
        if ccount % 10 == 0:  # every 10 chats
            yn = console.input("Summarize the chat to save tokens? [Yes/No]: ").strip().lower()
            if yn in ["yes", "y", "yes."]:
                try:
                    last_10_messages = get_last_messages(limit=10)
                except Exception as e:
                    console.print(f"[red] No messages to summarize[/red]")
                    continue
                else:
                    summary_prompt = "Summarize these messages concisely:\n"
                    for msg in last_10_messages:
                        summary_prompt += f"{msg['role']}:{msg['content']}\n"

                    # Call summarize using the prompt
                    summary_text = summarize(custom_prompt=summary_prompt)
                    console.print("Summarized chat:")
                    console.print(f"[grey93]{summary_text}[/grey93]") 
            else:
                console.print("Skipping summarization for next ten messages.")

        
if __name__ == "__main__":
    try:
        tars()
    except KeyboardInterrupt:
        console.print("\n[bold red]TARS SHUTDOWN SUCCESSFUL[/bold red]", justify="center")
    except Exception as e:
        console.print(f"Error occured: {e}")
        sys.exit(1)
