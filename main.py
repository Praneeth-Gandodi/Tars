import os
import json
import sys
from dotenv import load_dotenv, set_key
from groq import Groq
from rich.console import Console
from rich.panel import Panel
from stt import Audio
from supporter import *
from db import create_tables
from db import (
    save_user_message,
    save_assistant_message,
    save_tool_call,
    save_tool_response,
    get_or_create_model,
    create_new_session,
    end_session,
    get_session_by_id
)

if not os.path.exists(f"{os.getcwd()}/tars.db"):
    console.print("[yellow]Database not found. Creating the Database[/yellow]")
    create_tables()
    console.print("[green]Database created successfully[/green]")

    
    
load_dotenv()   
console = Console()

if not os.getenv("groq_api"):
    console.print("[red]Error: groq_api key not found in environment[/red]")
    groq_api = console.input("[yellow]Enter your Groq API key : [/yellow]")
    set_key(".env", "groq_api", groq_api)
    console.print("[green]Api key added to the .env file successfully[/green]")
    load_dotenv()
if not os.getenv("model"):
    console.print("[red]Error: Model not specified.[/red]")
    model = console.input("[yellow]Model ID ([link=https://console.groq.com/docs/models][blue underline]list[/blue underline][/link], blank = default): [/yellow]")
    if model:
        set_key(".env", "model", model)
        console.print(f"[green]{model} model is set successfully.")
        load_dotenv()
    else:
        model = "openai/gpt-oss-120b"
        set_key(".env", "model", model)
        console.print(f"[green]Default model: {model} is set successfully.")
        load_dotenv()



client = Groq(api_key=os.getenv("groq_api"))
model = os.getenv("model")
ccount = 0
chat = ""
current_session_id = None


try:
    with open('./tools.json', 'r') as f:
        tools = json.load(f)
except FileNotFoundError:
    console.print("[red]Error: tools.json does not exist[/red]")
    sys.exit()
except json.JSONDecodeError as e:
    console.print()


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
        if user_input.lower() in["q", "quit", "exit", "stop"]:
            end_session(current_session_id)
            return "exit"
        
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
    
    console.print("[green] Automatic Summarizer", justify="center", style="dim")

    return chat_summary

## Tools calling - MAIN LOGIC FOR TOOL CALLS.
def tool_calling(m_chat):
    global user_conversation_id
    global current_session_id
    global model_id
    console.print("Tool calling : ", style="dim")
    
    
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
    
            console.print(f"[dark_sea_green4]Making a call to the tool [bright_green]\"{function_name.strip('{}')}\" [/bright_green] function with the arguments: [bright_green]\"{f_args}\"[/bright_green][/dark_sea_green4]", style="dim")
            # Executing the function
            try:
                function_response = f_to_call(**f_args)
            except TypeError as e:
                function_response = f"Error: Invalid arguements passed for the function {e}"
            except Exception as e:
                function_response = f"Error: An Exception occured {e}"
                

            console.print(function_response, style="dim")
            
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
    
    # Making the second API call to give the data to the LLM
    console.print("[green dim]Processing the data[/green dim]")
    
    # First, make a non streaming call to check if the model wants to use another tool
    try:
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
        console.print("\n[yellow]Model requesting another tool call...[/yellow]", style="dim")
        return tool_calling(response_message)
    else:
        final_text = response_message.content
        Chat_completion.append({
            "role": "assistant",
            "content": final_text
        })
        
        #Save assistant message to the db 
        save_assistant_message(final_text, current_session_id, model_id=model_id)
        return final_text  

def text_input():
    inp = console.input("[green]>> [/green]")
    if inp.strip() == "":
        text_input()
    if inp.lower().strip(".") in ["clear", "clear the screen"]:
        return clear_console()
    return inp
