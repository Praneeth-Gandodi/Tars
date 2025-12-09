import os
import json
from dotenv import load_dotenv
from groq import Groq
from rich.console import Console
from stt import Audio
from weather import get_weather
from DateTime import get_datetime


load_dotenv()
console = Console()
client = Groq(api_key=os.getenv("groq_api"))
model = os.getenv("model")
ccount = 0
chat = ""

## Loading json
with open('./tools.json', 'r') as f:
    tools = json.load(f)

## Chat History 
Chat_completion = [
    {
    "role": "system",
    "content": "You are TARS, an AI assistant. Answer questions accurately and concisely. Do not add fictional scenarios, spacecraft references, or movie-related context unless specifically asked."
    }
]

## Available Functions
available_functions = {
    "get_weather": get_weather, 
    "get_datetime": get_datetime
}

## AI responses
def get_ai():
    global Chat_completion
    global ccount

    console.print("[green] TARS ACTIVATED", justify="center")
    while True:
        user_input = Audio()
        if user_input.lower() in["q", "quit", "exit", "stop"]:
            return "exit"
        Chat_completion.append({"role": "user",
                                "content": user_input}
                            )
        response = client.chat.completions.create(
            messages = Chat_completion,
            model = model,
            tools = tools,
            tool_choice="auto",
            stop = None,
            stream = False
        )
        response_message = response.choices[0].message
        final_text = ""
        if response_message.tool_calls:
            final_text = tool_calling(response_message)
            return final_text
        else:      
            final_text = response_message.content      
            print()
            console.print("[bold green]TARS:[/bold green]", end=" ")
            Chat_completion.append({
                "role": "assistant",
                "content": final_text
            })
            return final_text
  
## Chat Summarizer    
def summarize():
    global Chat_completion
    global ccount
    Chat_completion.append({"role": "user",
                            "content":"Summarize our previous conversation in few concise sentences. Focus only on the factual information discussed. Do not add roleplay elements, character references, or fictional context."}
                        )
    cresponse = client.chat.completions.create(
        messages = Chat_completion,
        model = model
    )
    chat = cresponse.choices[0].message.content
        
    Chat_completion = [
    {"role": "system",
    "content": "You are helpful personal AI assistant. Your name is Tars (from the movie Interstellar)."}
    ]
    Chat_completion.append({
    "role": "assistant",
    "content": chat
    })
    console.print("[green] Automatic Summarizer", justify="center")
    return chat

## Tools calling - has many comments because i dont remeber this logic that well 
def tool_calling(m_chat):
    console.print("[cyan].....TARS calling a tool.....", justify="center")
    ##Adding the history to the chat 
    Chat_completion.append(m_chat)
    
    # creting chat_buffer to collect the streaming reply
    chat_buffer = ""
    
    ## gets tool name and execute the function
    for tool_call in m_chat.tool_calls:
        function_name = tool_call.function.name
        
        ##checking if that tool/function exists or not 
        if function_name in available_functions:
            f_to_call = available_functions[function_name]
            f_args = json.loads(tool_call.function.arguments)
            
            console.print(f"[cyan] Calling the tool {function_name} with the arguments {f_args}[/cyan]")
            
            ##Excecuting the function
            function_response = f_to_call(**f_args)

            ##Printing the functions response 
            console.print(f"[dark_slate_gray2] {function_response} [/dark_slate_gray2]")
            
            ## Returning the actual conversation to the chat 
            Chat_completion.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": function_name,
                "content": json.dumps(function_response)
            })
        else:
            ## When the tool that model requested doesnt exist
            Chat_completion.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": function_name,
                "content": json.dumps({"error": f"Function {function_name} not found"})
            })
            
        ## Making the second api call the LLM to give it the data 
        console.print("\n[yellow]Second API call the LLM to analyze the function reply[/yellow]")
        stream = client.chat.completions.create(
            messages=Chat_completion,
            model=model,
            stop= None,
            stream = True
        )
        ## Getting the reply
        for chuck in stream:
            content = chuck.choices[0].delta.content
            if  content:
                chat_buffer += content
        Chat_completion.append({
        "role": "assistant",
        "content": chat_buffer
        })
        return chat_buffer     
                       
            
            
            



        