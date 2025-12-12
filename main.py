import os
import json
from dotenv import load_dotenv
from groq import Groq
from rich.console import Console
from stt import Audio
from tools.weather import get_weather
from tools.DateTime import get_datetime
from tools.news import get_news
from tools.wiki import *
from tools.websearch import *
from tools.video_download import * 


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
    "content": (
        "You are TARS, an AI assistant. Answer questions accurately and concisely. "
        "Do not add fictional scenarios or movie context. "
        "**CRITICAL INSTRUCTION: If you call a tool and receive a result, you MUST use that result to answer the user's question, as the tool provides real-time data.**"
    )
    }
]

## Available Functions
available_functions = {
    "get_weather": get_weather, 
    "get_datetime": get_datetime,
    "get_news": get_news,
    "wiki_search": wiki_search,
    "wiki_summary": wiki_summary,
    "wiki_content": wiki_content,
    "web_search":web_search,
    "image_search":image_search,
    "video_search":video_search,
    "news_search": news_search,
    "yt_info": yt_info,
    "yt_videoDownload": yt_videoDownload,
    "yt_AudioDownload" : yt_AudioDownload,
    "ig_download": ig_download,
    "fb_download": fb_download
}

## AI responses
def get_ai(func):
    global Chat_completion
    while True:
        user_input = func()
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

## Tools calling - This section has too many comments because i dont remeber this logic that well 

def tool_calling(m_chat):
    console.print("Tool calling : ", style="dim")
    # Adding the history to the chat
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
            
            console.print(f"[cyan]Making a call to the tool {function_name} with the arguments {f_args}[/cyan]", style="dim")
            
            # Executing the function
            function_response = f_to_call(**f_args)
            
            # Printing the function's response
            console.print(function_response, style="dim")
            
            # Returning the actual conversation to the chat
            Chat_completion.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": function_name,
                "content": json.dumps(function_response)
            })
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
    # First, make a non-streaming call to check if the model wants to use another tool
    response = client.chat.completions.create(
        messages=Chat_completion,
        model=model,
        tools=tools,
        tool_choice="auto",
        stop=None,
        stream=False
    )
    
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
        
        return final_text  

def text_input():
    inp = console.input("[green]>> You: [/green]")
    return inp
