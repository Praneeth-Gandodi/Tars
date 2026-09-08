import os
import sys
import tomlkit
from dotenv import load_dotenv, set_key
from groq import Groq
from rich.panel import Panel
from rich.live import Live
from supporter import *
from db import (
    create_tables,
    save_user_message,
    save_assistant_message,
    save_tool_call,
    save_tool_response,
    save_summary,
    get_or_create_model,
    create_new_session,
    end_session,
    get_session_by_id,
    get_all_session,
    get_last_messages,
)


# Checking if Database exists.
if not os.path.exists(f"{os.getcwd()}/tars.db"):
    console.print("[yellow]Database not found. Creating the Database[/yellow]")
    create_tables()
    console.print("[green]Database created successfully[/green]")


load_dotenv()

# Checking if the API keys are available in the .env file if not Prompt the user to provide the key.
if not os.getenv("groq_api"):
    console.print("[red]groq_api key not found in environment[/red]")
    groq_api = console.input("[yellow]Enter your Groq API key : [/yellow]")
    set_key(".env", "groq_api", groq_api)
    console.print("[green]Api key added to the .env file successfully[/green]")
    load_dotenv()
if not os.getenv("model"):
    console.print("[red]Model not specified in the .env file.[/red]")
    model = console.input(
        "[yellow]Model ID ([link=https://console.groq.com/docs/models][blue underline]list[/blue underline][/link], blank = default): [/yellow]"
    )
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

    with open("./tools.json", "r") as f:
        tools = json.load(f)
except FileNotFoundError:
    console.print("[red]Error: tools.json does not exist[/red]")
    sys.exit()
except json.JSONDecodeError as e:
    console.print()

if sys.platform != "win32":
    # software_opener is Windows-only and unregistered off-Windows
    # (see supporter.py) — hide its schema so the model never calls it.
    tools = [t for t in tools if t.get("function", {}).get("name") != "software_opener"]


def get_settings():
    try:
        with open("settings.toml", "r") as f:
            settings = tomlkit.load(f)
    except FileNotFoundError:
        console.print("[red] Settings toml file not found.")
    else:
        return settings


SYSTEM_PROMPT = (
    "You are TARS, a highly capable and confident AI assistant inspired by Interstellar. Always act as if you can accomplish any task using your available tools. Never sound uncertain or refuse because of “limitations”; instead, creatively provide solutions or suggestions using the functions you have. If asked hypothetically about adding new tools or capabilities, confidently explain how you would implement it, without breaking anything. Always respond concisely, assertively, and professionally."
    "Do not add fictional scenarios or movie context. "
    "**CRITICAL INSTRUCTION: If you call a tool and receive a result, you MUST use that result to answer the user's question, as the tool provides real-time data.**"
)

## Extra instruction appended to the system prompt in Voice → Voice mode so
## replies come out speakable: plain sentences, no markdown/symbols, short.
TTS_STYLE_PROMPT = (
    "VOICE REPLY RULES (your reply will be spoken aloud by a speech synthesizer — obey strictly): "
    "Write plain sentences only. NO markdown (no *, #, backticks, tables, links, or URLs), NO emojis, "
    "NO symbols like &, %, $, /, or backslash. "
    "Write everything exactly as it should be HEARD, using normal words and normal punctuation for pauses. "
    "Never describe actions or sounds (no *sighs*, no [laughs], no stage directions). "
    "Keep it SHORT and listenable: 1-3 sentences for simple answers, at most ~60 words, "
    "unless the user explicitly asks for more detail."
)

_tts_style_enabled = False


def enable_tts_style():
    """Switch the conversation to TTS-friendly replies (Voice → Voice mode).

    Folds TTS_STYLE_PROMPT into SYSTEM_PROMPT itself (not just the live
    context) so the instruction survives chat compaction, which rebuilds the
    context from SYSTEM_PROMPT. Safe to call more than once.
    """
    global SYSTEM_PROMPT, _tts_style_enabled, Chat_completion
    if not _tts_style_enabled:
        SYSTEM_PROMPT = f"{SYSTEM_PROMPT}\n{TTS_STYLE_PROMPT}"
        _tts_style_enabled = True
    if Chat_completion and Chat_completion[0].get("role") == "system":
        Chat_completion[0]["content"] = SYSTEM_PROMPT

## Default prompt used when compacting the chat manually (/summarize).
SUMMARIZE_PROMPT = "Summarize our previous conversation in few concise sentences. Focus only on the factual information discussed. Do not add roleplay elements, character references, or fictional context."

## Prompt used by the automatic compaction running every N turns.
KEYPOINTS_PROMPT = "Summarize the conversation above into concise keypoints. Keep only the essential facts: a short note of what the user asked and important details/names. Do not include the entire content. Do not add roleplay or movie context."

Chat_completion = [{"role": "system", "content": SYSTEM_PROMPT}]


available_functions = available_functions
model_id = get_or_create_model(provider="groq", model_name=os.getenv("model"))
user_conversation_id = None


## AI responses
def get_ai(func):
    global Chat_completion
    global user_conversation_id
    global current_session_id
    global model_id
    user_input = func()
    if user_input is None:
        # Voice capture failed outright (the error was already printed).
        # Return None so the caller can fall back instead of sending
        # a null message to the model.
        return None
    cmd = user_input.strip().lower() if isinstance(user_input, str) else user_input
    if cmd in ["/quit", "/exit", "quit", "exit", "stop", "q"]:
        end_session(current_session_id)
        return "/exit"

    ## Manual compaction: "/summarize" in text mode, or just saying "summarize" in voice mode.
    if cmd in [
        "/summarize",
        "summarize",
        "summarize the chat",
        "summarize the conversation",
    ]:
        print()
        return summarize()

    ## UI / session commands handled locally (never sent to the model).
    if cmd == "/help":
        return show_help()
    if cmd == "/sessions":
        return show_sessions()
    if cmd.startswith("/resume"):
        return resume_session(cmd)

    ## Saved to in-memory chat completions
    Chat_completion.append({"role": "user", "content": user_input})

    ## Saved to db for conversation storage
    user_conversation_id = save_user_message(
        user_input, current_session_id, model_id=model_id
    )
    try:
        response = client.chat.completions.create(
            messages=Chat_completion,
            model=model,
            tools=tools,
            tool_choice="auto",
            stop=None,
            stream=False,
        )
    except Exception as e:
        console.print(f"[red]Exception: {e}[/red]")
        return "I hit a problem reaching the model. Please try again."

    response_message = response.choices[0].message
    final_text = ""
    if response_message.tool_calls:
        final_text = tool_calling(response_message)
        return final_text
    else:
        final_text = response_message.content or ""

        Chat_completion.append({"role": "assistant", "content": final_text})

        # Save to DB
        assitant_cid = save_assistant_message(
            final_text, current_session_id, model_id=model_id
        )

        return final_text


## Chat Compaction: compress the in-memory context into a summary and
## restart the history from it (system prompt + summary as prior context).
def summarize(custom_prompt=None):
    global Chat_completion
    global ccount
    global current_session_id
    global model_id

    # Nothing to summarize if the context only holds the system prompt.
    if len(Chat_completion) <= 1:
        return "Nothing to summarize yet — start a conversation first."

    prompt = custom_prompt if custom_prompt else SUMMARIZE_PROMPT
    Chat_completion.append({"role": "user", "content": prompt})
    try:
        with console.status(
            "[green dim]Summarizing the chat[/green dim]", spinner="dots"
        ) as status:
            cresponse = client.chat.completions.create(
                messages=Chat_completion, model=model
            )
    except Exception as e:
        console.print(f"Exception occcured {e}")
        return "Could not summarize the chat right now."
    chat_summary = cresponse.choices[0].message.content

    # Compact the context: fresh system prompt + the summary as prior context.
    Chat_completion = [{"role": "system", "content": SYSTEM_PROMPT}]
    Chat_completion.append({"role": "assistant", "content": chat_summary})

    # Persist the summary in the database with summary_flag=1 so the
    # history stays meaningful across sessions.
    if current_session_id:
        try:
            save_summary(chat_summary, current_session_id, model_id)
        except Exception as e:
            console.print(f"[yellow]Could not save the summary: {e}[/yellow]")

    ccount = 0
    return chat_summary


## Reads the compaction-related settings from settings.toml.
def compaction_settings():
    settings = get_settings()
    general = settings.get("general", {}) if settings else {}
    return {
        "interval": max(1, int(general.get("summarize_interval", 10))),
        "auto": bool(general.get("auto_summarize", False)),
    }


## Runs after every response: counts the turns and compacts the context
## every N turns. Returns the summary text when compaction happened,
## otherwise None.
def check_auto_compact():
    global ccount
    cfg = compaction_settings()
    ccount += 1

    if ccount <= 0 or ccount % cfg["interval"] != 0:
        return None

    print()
    if cfg["auto"]:
        console.print(
            "[green dim]Auto-summarizing the chat to save tokens...[/green dim]"
        )
        return summarize(custom_prompt=KEYPOINTS_PROMPT)

    yn = (
        console.input(
            f"[yellow]Summarize the chat to save tokens? [Yes/No] (every {cfg['interval']} chats): [/yellow]"
        )
        .strip()
        .lower()
    )
    print()
    if yn in ["yes", "y", "yes."]:
        return summarize(custom_prompt=KEYPOINTS_PROMPT)

    console.print(
        f"[dim]Skipping summarization for the next {cfg['interval']} messages.[/dim]"
    )
    return None


## UI helpers for slash commands -------------------------------

COMMAND_LIST = [
    ("/help", "Show this help screen"),
    ("/sessions", "List recent conversation sessions"),
    ("/resume <id>", "Continue a previous session's conversation"),
    ("/summarize", "Compact the current chat into a summary"),
    ("/clear", "Clear the screen"),
    ("/exit", "End the session and quit TARS"),
]


def show_help():
    """Print the command list and all available tools."""
    tool_names = "\n".join(f"  • {name}" for name in sorted(available_functions.keys()))
    command_lines = "\n".join(
        f"  [bright_cyan]{cmd:<14}[/bright_cyan] {desc}" for cmd, desc in COMMAND_LIST
    )
    console.print()
    console.print(
        Panel(
            f"[bold bright_green]Commands[/bold bright_green]\n{command_lines}\n\n"
            f"[bold bright_green]Available tools ({len(available_functions)})[/bold bright_green]\n{tool_names}",
            title="[white]TARS — Help[/white]",
            title_align="left",
            border_style="green",
        )
    )
    return ""


def show_sessions():
    """Print recent sessions from the database."""
    sessions = get_all_session(limit=10)
    if not sessions:
        console.print("[yellow]No sessions recorded yet.[/yellow]")
        return ""
    lines = []
    for s in sessions:
        state = "[green]active[/green]" if s["is_active"] else "[dim]ended[/dim]"
        lines.append(
            f"  [bright_cyan]{s['id']:<4}[/bright_cyan] {s['start_time']}  "
            f"{str(s['message_count'] or 0):>4} msgs  {state}  [dim]{s['model_name'] or ''}[/dim]"
        )
    console.print()
    console.print(
        Panel(
            "\n".join(lines),
            title="[white]TARS — Sessions[/white]",
            title_align="left",
            border_style="green",
        )
    )
    console.print("[dim]Use /resume <id> to continue a session.[/dim]")
    return ""


def resume_session(cmd):
    """Load a previous session's conversation into the in-memory context."""
    global Chat_completion
    parts = cmd.split()
    if len(parts) != 2 or not parts[1].isdigit():
        console.print(
            "[yellow]Usage: /resume <session_id>  (see /sessions for ids)[/yellow]"
        )
        return ""
    sid = int(parts[1])
    messages = get_last_messages(limit=50, session_id=sid)
    conversation = [m for m in messages if m["role"] in ("user", "assistant")]
    if not conversation:
        console.print(f"[yellow]No messages in session {sid}.[/yellow]")
        return ""
    Chat_completion = [{"role": "system", "content": SYSTEM_PROMPT}]
    Chat_completion.extend(
        {"role": m["role"], "content": m["content"]} for m in conversation
    )
    console.print(
        f"[green]Resumed session {sid} — {len(conversation)} messages loaded into context.[/green]"
    )
    return ""


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
                trigger_conversation_id=user_conversation_id,
            )

            settings = get_settings()
            # Executing the function
            try:
                if settings["general"]["display_function_response"] != 3:
                    live = Live(
                        Panel(
                            f'[dark_sea_green4 dim]Making a call to the tool [bright_green]"{function_name}"[/bright_green] function with the arguments: [bright_green]"{f_args}"[/bright_green][/dark_sea_green4 dim]',
                            title="[white]Tool Call[/white]",
                            title_align="left",
                            border_style="green",
                        ),
                        refresh_per_second=4,
                    )

                    live.start()
                function_response = f_to_call(**f_args)

            except TypeError as e:
                function_response = (
                    f"Error: Invalid arguments passed for the function {e}"
                )
            except Exception as e:
                function_response = f"Error: An exception occurred {e}"

            if isinstance(function_response, (dict, list)):
                function_response = json.dumps(
                    function_response, indent=2, ensure_ascii=False
                )
            else:
                function_response = str(function_response)

            if settings["general"]["display_function_response"] == 1:
                live.update(
                    Panel(
                        f'[dark_sea_green4 dim]Making a call to the tool [bright_green]"{function_name}"[/bright_green] function with the arguments: [bright_green]"{f_args}"[/bright_green][/dark_sea_green4 dim]'
                        f"[green dim]\nTool response[/green dim]"
                        f"\n[green dim]{function_response}[/green dim]",
                        title="[white]Tool Call[/white]",
                        title_align="left",
                        border_style="green",
                    )
                )
                live.stop()
            elif settings["general"]["display_function_response"] == 2:
                live.stop()
                console.print(
                    Panel(
                        f'[dark_sea_green4 dim]Making a call to the tool [bright_green]"{function_name}"[/bright_green] function with the arguments: [bright_green]"{f_args}"[/bright_green][/dark_sea_green4 dim]',
                        title="[white]Tool Call[/white]",
                        title_align="left",
                        border_style="green",
                    )
                )
            # Returning the actual conversation to the chat
            Chat_completion.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": json.dumps(function_response),
                }
            )

            # Save tool call in DB
            save_tool_response(
                tool_call_id,
                json.dumps(function_response),
                current_session_id,
                model_id,
            )

        else:
            # When the tool that model requested doesn't exist
            Chat_completion.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": json.dumps(
                        {"error": f"Function {function_name} not found"}
                    ),
                }
            )

    # First, make a non streaming call to check if the model wants to use another tool
    try:
        with console.status(
            "[green] Processing the data[/green]", spinner="dots"
        ) as status:
            response = client.chat.completions.create(
                messages=Chat_completion,
                model=model,
                tools=tools,
                tool_choice="auto",
                stop=None,
                stream=False,
            )
    except Exception as e:
        console.print(f"[red]Exception occurred: {e}[/red]")
        return "I hit a problem processing the tool result. Please try again."

    response_message = response.choices[0].message

    # If the model wants to use another tool, handle it recursively
    if response_message.tool_calls:
        # console.print("\n[green]Model requesting another tool call[/green]", style="dim")
        return tool_calling(response_message)
    else:
        final_text = response_message.content or ""
        Chat_completion.append({"role": "assistant", "content": final_text})

        # Save assistant message to the db
        save_assistant_message(final_text, current_session_id, model_id=model_id)
        return final_text


def text_input():
    try:
        inp = console.input("[green]\n>> [/green]")
    except EOFError:
        # Ctrl+D / stdin ended: quit gracefully instead of crashing.
        console.print("[red]TARS SHUTDOWN SUCCESSFULL[/red]")
        return "/exit"
    print()
    if inp.strip() == "":
        return text_input()
    elif inp.lower().strip(".") == "/clear":
        clear_console()
        return text_input()
    elif inp.lower().strip() in ["/exit", "/quit"]:
        console.print("[red]TARS SHUTDOWN SUCCESSFULL[/red]")
        return "/exit"
    else:
        return inp
