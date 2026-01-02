import logging
import sys
import main
from main import *
from styling import starting, input_type
from rich.markdown import Markdown
from rich.panel import Panel
from rich.spinner import Spinner
from supporter import *
from db import *



## To stop the printing of logging in the terminal.
logging.getLogger().setLevel(logging.CRITICAL)
logging.getLogger("RealtimeSTT").setLevel(logging.CRITICAL)
logging.getLogger("faster_whisper").setLevel(logging.CRITICAL)
logging.getLogger("httpx").setLevel(logging.CRITICAL)
logging.getLogger("httpcore").setLevel(logging.CRITICAL)

def tars():
    global ccount
    audio_reply = False
    starting()
    
    main.current_session_id = create_new_session(main.model_id)
    session_info = get_session_by_id(main.current_session_id)
    opt = input_type()
    
    if opt == "1":
        func = text_input
    elif opt == "3":
        try:
            with console.status("[green dim]Importing STT module[/green dim]", spinner="dots") as status:
                from speech_to_text import Audio
        except ImportError as e:
            console.print(f"[red dim]Error: {e}[/red dim]")
        func = Audio
    elif opt == "2":
        try:
            with console.status("[green dim]Importing STT & TTS modules [/green dim]", spinner="dots") as status:
                from speech_to_text import Audio
                from text_to_speech import tts_pipeline
        except ImportError as e:
            console.print(f"[red dim]Error: {e}[/red dim]")
        func = Audio
        audio_reply = True
    else:
        console.print("[red]Invalid choice[/red]")
        return
    
    while True:
        status = get_ai(func)
        # if status == None:
        #     func = text_input      
        if status == "/exit":
            end_session(main.current_session_id)
            sys.exit(1)
        elif status.lower() == "/summarize":
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
            
        try:
            md = Markdown(status)
            ccount += 1
            console.print(
                Panel(
                md, title="[white]Tars[/white]",
                subtitle=f"[white]~ {ccount}[/white]",
                subtitle_align="right",
                title_align="left",
                border_style="green" ),
                overflow="fold",
                no_wrap=False)
            print()
            if audio_reply:
                tts_pipeline(text=status)
        except Exception as e:
            console.print(status)
                    
        
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
