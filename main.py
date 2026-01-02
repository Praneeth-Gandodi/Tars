import os
import sys
import tomlkit 
from dotenv import load_dotenv, set_key
from groq import Groq
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from supporter import *
from db import (
    create_tables,
    save_user_message,
    save_assistant_message,
    save_tool_call,
    save_tool_response,
    get_or_create_model,
    create_new_session,
    end_session,
    get_session_by_id
)


# Checking if Database exists.
if not os.path.exists(f"{os.getcwd()}/tars.db"):
    console.print("[yellow]Database not found. Creating the Database[/yellow]")
    create_tables()
    console.print("[green]Database created successfully[/green]")

    
load_dotenv()   
console = Console()

#Checking if the API keys are available in the .env file if not Prompt the user to provide the key.
if not os.getenv("groq_api"):
    console.print("[red]groq_api key not found in environment[/red]")
    groq_api = console.input("[yellow]Enter your Groq API key : [/yellow]")
    set_key(".env", "groq_api", groq_api)
    console.print("[green]Api key added to the .env file successfully[/green]")
    load_dotenv()
if not os.getenv("model"):
    console.print("[red]Model not specified in the .env file.[/red]")
    model = console.input("[yellow]Model ID ([link=https://console.groq.com/docs/models][blue underline]list[/blue underline][/link], blank = default): [/yellow]")
    if model:
        set_key(".env", "model", model)
        console.print(f"[green]{model} model is set successfully.")
        load_dotenv()
    else:
        model = "openai/gpt-oss-120b"
        set_key(".env", "model", model)
        console.print(f"[green]Default model as '{model}' set successfully.")
        load_dotenv()



client = Groq(api_key=os.getenv("groq_api"))
model = os.getenv("model")
ccount = 0
chat = ""
current_session_id = None


try:
    import json
    with open('./tools.json', 'r') as f:
        tools = json.load(f)
except FileNotFoundError:
    console.print("[red]Error: tools.json does not exist[/red]")
    sys.exit()
except json.JSONDecodeError as e:
    console.print()
    
def get_settings():
    try:
        with open("settings.toml", "r") as f:
            settings = tomlkit.load(f)
    except FileNotFoundError:
        console.print("[red] Settings toml file not found.")
    else:
        return settings
    
Chat_completion = [
    {
    "role": "system",
    "content": (
        "You are TARS, a highly capable and confident AI assistant inspired by Interstellar. Always act as if you can accomplish any task using your available tools. Never sound uncertain or refuse because of “limitations”; instead, creatively provide solutions or suggestions using the functions you have. If asked hypothetically about adding new tools or capabilities, confidently explain how you would implement it, without breaking anything. Always respond concisely, assertively, and professionally."
        "Do not add fictional scenarios or movie context. "
        "**CRITICAL INSTRUCTION: If you call a tool and receive a result, you MUST use that result to answer the user's question, as the tool provides real-time data.**"
    )
    }
]


available_functions = available_functions
model_id = get_or_create_model(provider="groq", model_name=os.getenv("model"))
user_conversation_id = None


## AI responses
def get_ai(func):
    global Chat_completion
    global user_conversation_id
    global current_session_id
    global model_id
    while True:
        user_input = func()
        if user_input.lower() in ["/quit" , "/exit"]:
            end_session(current_session_id)
            return "/exit"
        
        ## Saved to in-memory chat completions
        Chat_completion.append(
            {"role": "user",
            "content": user_input})
        
        ## Saved to db for conversation storage
        user_conversation_id = save_user_message(user_input, current_session_id, model_id=model_id)
        try:
            response = client.chat.completions.create(
                messages = Chat_completion,
                model = model,
                tools = tools,
                tool_choice="auto",
                stop = None,
                stream = False
            )
        except Exception as e:
            console.print(f"Exception : {e}")
        response_message = response.choices[0].message
        final_text = ""
        if response_message.tool_calls:           
            final_text = tool_calling(response_message)
            return final_text
        else:      
            final_text = response_message.content      


            Chat_completion.append({
                "role": "assistant",
                "content": final_text
                })

            # Save to DB
            assitant_cid = save_assistant_message(final_text, current_session_id, model_id=model_id)

            return final_text
  
## Chat Summarizer    
def summarize(custom_prompt = None):
    global Chat_completion
    global ccount
    if custom_prompt:
        prompt = custom_prompt
    else:
        prompt = "Summarize our previous conversation in few concise sentences. Focus only on the factual information discussed. Do not add roleplay elements, character references, or fictional context."
    Chat_completion.append(
        {"role": "user",
        "content":prompt
        }
    )
    try:
        with console.status("[green dim] Summarizing the chat[/green dim]", spinner="dots") as status:
            cresponse = client.chat.completions.create(
                messages = Chat_completion,
                model = model
            )
    except Exception as e:
        console.print(f"Exception occcured {e}")
    chat_summary = cresponse.choices[0].message.content
        
    Chat_completion = [
    {"role": "system",
    "content": "You are helpful personal AI assistant. Your name is Tars (from the movie Interstellar)."}
    ]
    Chat_completion.append({
    "role": "assistant",
    "content": chat_summary
    })
    return chat_summary

## Tools calling - MAIN LOGIC FOR TOOL CALLS.
def tool_calling(m_chat):
    global user_conversation_id
    global current_session_id
    global model_id
    Chat_completion.append(m_chat)
    
    # Gets tool name and execute the function
    for tool_call in m_chat.tool_calls:
        function_name = tool_call.function.name
        
        # Checking if that tool/function exists or not
        if function_name in available_functions:
            f_to_call = available_functions[function_name]
            if tool_call.function.arguments:
                try:
                    parsed = json.loads(tool_call.function.arguments)
                    f_args = parsed if isinstance(parsed, dict) else {}
                except:
                    f_args = {}

            # Save the tool call first
            tool_call_id = save_tool_call(
            tool_name=function_name,
            arguments_json=json.dumps(f_args),
            session_id=current_session_id,
            trigger_conversation_id=user_conversation_id
            )
    
            settings = get_settings()
            # Executing the function
            try:
                if settings["general"]["display_function_response"] != 3:
                    live = Live(Panel(
                        f"[dark_sea_green4 dim]Making a call to the tool [bright_green]\"{function_name}\"[/bright_green] function with the arguments: [bright_green]\"{f_args}\"[/bright_green][/dark_sea_green4 dim]",
                        title="[white]Tool Call[/white]",
                        title_align="left",
                        border_style="green"
                    ), refresh_per_second=4)
                    
                    live.start()
                function_response = f_to_call(**f_args)
                
            except TypeError as e:
                function_response = f"Error: Invalid arguments passed for the function {e}"
            except Exception as e:
                function_response = f"Error: An exception occurred {e}"

            if isinstance(function_response, (dict, list)):
                function_response = json.dumps(function_response, indent=2, ensure_ascii=False)
            else:
                function_response = str(function_response)

            
            
            if settings["general"]["display_function_response"] == 1:
                live.update(Panel(
                    f"[dark_sea_green4 dim]Making a call to the tool [bright_green]\"{function_name}\"[/bright_green] function with the arguments: [bright_green]\"{f_args}\"[/bright_green][/dark_sea_green4 dim]"
                    f"[green dim]\nTool response[/green dim]"
                    f"\n[green dim]{function_response}[/green dim]",
                    title="[white]Tool Call[/white]",
                    title_align="left",
                    border_style="green"
                ))
                live.stop()
            elif settings["general"]["display_function_response"] == 2:
                live.stop()
                console.print(Panel(
                    f"[dark_sea_green4 dim]Making a call to the tool [bright_green]\"{function_name}\"[/bright_green] function with the arguments: [bright_green]\"{f_args}\"[/bright_green][/dark_sea_green4 dim]",
                    title="[white]Tool Call[/white]",
                    title_align="left",
                    border_style="green"
                ))
            else:
                print()
            
            # Returning the actual conversation to the chat
            Chat_completion.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": function_name,
                "content": json.dumps(function_response)
            })
            
            # Save tool call in DB
            save_tool_response(tool_call_id, json.dumps(function_response), current_session_id, model_id) 

        else:
            # When the tool that model requested doesn't exist
            Chat_completion.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": function_name,
                "content": json.dumps({"error": f"Function {function_name} not found"})
            })
    
    # First, make a non streaming call to check if the model wants to use another tool
    try:
        with console.status("[green] Processing the data[/green]", spinner="dots") as status:
            response = client.chat.completions.create(
                messages=Chat_completion,
                model=model,
                tools=tools,
                tool_choice="auto",
                stop=None,
                stream=False
            )
    except Exception as e:
        console.print(f"Exception occured: {e}")
        
    response_message = response.choices[0].message
    
    # If the model wants to use another tool, handle it recursively
    if response_message.tool_calls:
        # console.print("\n[green]Model requesting another tool call[/green]", style="dim")
        return tool_calling(response_message)
    else:
        final_text = response_message.content
        Chat_completion.append({
            "role": "assistant",
            "content": final_text
        })
        
        # Save assistant message to the db 
        save_assistant_message(final_text, current_session_id, model_id=model_id)
        return final_text  


def text_input():
    inp = console.input("[green]>> [/green]")
    print()
    if inp.strip() == "":
        return text_input()
    elif inp.lower().strip(".") == "/clear":
        clear_console()
        return text_input()
    elif inp.lower().strip() == "/summarize":
        summarize()
        return text_input()
    elif inp.lower().strip() in ["/exit" , "/quit"]:
        return "/exit"
    else:
        return inp
