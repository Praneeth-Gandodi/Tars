import main
import logging
import sys
from main import get_ai, console, ccount, summarize, text_input
from styling import starting, input_type
from rich.markdown import Markdown
from stt import Audio
from supporter import *
from db import *




logging.getLogger().setLevel(logging.CRITICAL)
logging.getLogger("RealtimeSTT").setLevel(logging.CRITICAL)
logging.getLogger("faster_whisper").setLevel(logging.CRITICAL)
logging.getLogger("httpx").setLevel(logging.CRITICAL)
logging.getLogger("httpcore").setLevel(logging.CRITICAL)

def tars():
    global ccount
    starting()
    
    main.current_session_id = create_new_session(main.model_id)
    session_info = get_session_by_id(main.current_session_id)
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
            
        elif status in ["q", "quit", "exit", "stop"]:
            end_session(main.current_session_id)
            return 
        elif status.lower() == "summarize":
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
            console.print(md, overflow="fold", no_wrap=False)
        except Exception as e:
            console.print(status)
                    
        ccount += 1
        console.print(f"[grey46]message #[/grey46][deep_sky_blue1 dim]{ccount}[/deep_sky_blue1 dim]", justify="right")
        
        ## summarizin for every ten messages to reduce the usage of tokens.
        if ccount % 10 == 0:  # For every 10 chats
            yn = console.input("Summarize the chat to save tokens? [Yes/No]: ").strip().lower()
            if yn in ["yes", "y", "yes."]:
                try:
                    last_10_messages = get_last_messages(limit=10)
                except Exception as e:
                    console.print(f"[red] No messages to summarize[/red]")
                    continue
                else:
                    summary_prompt = "Summarize these messages concisely and in this summarization keep only keypoints not entire content like what user asked in short and name and some details :\n"
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
        end_session(main.current_session_id)
    except Exception as e:
        console.print(f"Error occured: {e}")
        end_session(main.current_session_id)
        sys.exit(1)
