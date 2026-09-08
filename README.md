# TARS — Voice AI Assistant

**TARS** is a terminal-based AI assistant that works in three modes — **Text → Text**, **Voice → Voice** (Speech-to-Text + Text-to-Speech with barge-in interruption), and **Voice → Text** — powered by the **Groq API** and **function calling** with 20+ built-in tools.

Built as a learning project: it covers offline speech recognition (RealtimeSTT / faster-whisper), offline speech synthesis (Piper TTS), SQLite persistence, context compaction, and browser automation.

---

## Features

### Interaction modes
- **Text → Text** — chat directly with the model
- **Voice → Voice** — speak to TARS, hear it reply, and interrupt it anytime by talking
- **Voice → Text** — speak, read the reply

### Tools (function calling)
1. **Web search** — DuckDuckGo text / image / video / news search
2. **Wikipedia** — search, summary, and full article content
3. **News** — headlines by category and country
4. **Weather** — current conditions for any city
5. **Date & time** — local and for any city
6. **Video downloader** — YouTube / Instagram / Facebook (yt-dlp)
7. **File handling** — read, write, search, and open files; create Word (.docx) documents
8. **Browser automation** — navigate pages, click, fill forms, extract text, take screenshots (Playwright)
9. **Memory** — persistent `memory.md` the model can read/write across sessions
10. **System info** — OS, CPU, RAM, disk, battery
11. **Speedtest, apps opener, browser opener, console clear** and more

### Smart conversation management
- **SQLite persistence** — sessions, messages, tool calls, and summaries are stored in `tars.db`
- **Auto compaction** — every N chats TARS compresses the context into a summary to save tokens (configurable; prompt-free or silent mode)
- **`/sessions` + `/resume`** — list past conversations and continue any of them

---

## Prerequisites

- A free Groq API key from <https://console.groq.com/keys>
- (Python 3.12 is installed **for you** by the installers below)

## Install

> **No Docker needed.** TARS installs natively on Windows, macOS, Linux and WSL2.
> The bundled Docker image is too large to share; the native setup below runs the
> same code everywhere and downloads only the deps + one speech model.
>
> **Full walkthrough:** see [`INSTALLATION.md`](INSTALLATION.md).

### One-command installer

One copy-paste per platform — the installer clones TARS (auto-switches to the
**`dev`** branch), installs **Python 3.12** if needed, system libraries, a
`.venv`, all Python deps, Chromium, and prompts for your Groq key:

```bash
# Windows (PowerShell):
Set-ExecutionPolicy -Scope Process Bypass
irm https://raw.githubusercontent.com/Praneeth-Gandodi/Tars/dev/install.ps1 | iex

# macOS / Linux / WSL2:
curl -fsSL https://raw.githubusercontent.com/Praneeth-Gandodi/Tars/dev/install.sh | bash
```

Idempotent — rerun any time to repair or upgrade; it simply picks up where it
left off.

### Manual setup

```bash
# 1. clone (or copy) the project
git clone https://github.com/Praneeth-Gandodi/Tars.git
cd Tars
git checkout dev                  # ← use the dev branch (has the install files)

# 2. virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 3. dependencies
pip install -r requirements.txt

# 4. optional: browser automation binaries (only needed for browser tools)
playwright install chromium

# 5. configure
cp .env.example .env      # then paste your Groq API key + model into .env
```

> On first voice use, TARS downloads the speech models automatically (STT model ~ hundreds of MB). Later runs use the cached copy.

## Run

If you used the one-command installer, TARS is in a `Tars` folder where you ran
it. Step inside and run:

```bash
cd Tars        # skip if you're already in the Tars folder
python tars.py
```

Choose a mode, then just talk or type. Type `/help` at any time to see commands and available tools.

### Commands

| Command | What it does |
|---|---|
| `/help` | Show commands + all available tools |
| `/sessions` | List recent sessions |
| `/resume <id>` | Continue a previous session |
| `/summarize` | Compact the current chat into a summary now |
| `/clear` | Clear the screen |
| `/exit` | End the session and quit |

---

## Docker (no installation)

The image bundles Python deps, the Piper TTS voice, and the whisper STT model, so **nothing is downloaded at runtime**.

```bash
# build once
docker build -t tars .

# text + voice modes (Linux / WSL2 with a sound card):
docker run -it --rm --device /dev/snd --shm-size=1g tars
```

- **Text mode** works on any host.
- **Voice modes** need a real audio device; Docker only exposes one on **Linux / WSL2** (`--device /dev/snd`). On Windows/macOS Docker Desktop, run the container for text mode only.
- `--shm-size=1g` is required for Chromium browser automation.

> **Running on Windows?** Follow [`WSL_DOCKER_GUIDE.md`](WSL_DOCKER_GUIDE.md) — it gets voice mode working via WSL2 + WSLg audio (Docker Engine inside WSL + PulseAudio socket mount).

---

## Architecture

```
tars.py          entry point — mode selection + main loop, markdown rendering
main.py          LLM orchestration — get_ai/tool_calling, context compaction, slash commands
supporter.py     tool registry (available_functions), console helpers
styling.py       startup banner + mode picker
speech_to_text.py  RealtimeSTT / faster-whisper, live transcript, barge-in event
text_to_speech.py  Piper TTS with interruptible playback
db.py            SQLite layer (sessions, conversations, tool_calls, models)
tools/           individual tools (web, wiki, news, files, browser, system…)
tools.json       OpenAI function-calling schemas sent to the model
```

1. `tars.py` asks the model for a response (`main.get_ai`).
2. If the model requests tools, `tool_calling` executes them via `supporter.available_functions`.
3. Every N chats, `check_auto_compact` summarizes the context and restarts from the summary (persisted with `summary_flag=1`).

---

## Configuration

- **`.env`** — API key and model (see `.env.example`).
- **`settings.toml`** — tool-call display mode, auto-summarize on/off, summarize interval, browser path.

---

## Implemented / Planned

- [x] Text-to-Speech (Piper) with barge-in interruption
- [x] Speech-to-Text (RealtimeSTT / faster-whisper)
- [x] Web / image / video / news search
- [x] News, Wikipedia, Weather, Date & Time, Speedtest
- [x] File handling (read, write, search, open, Word docs)
- [x] Video downloader (YouTube / Instagram / Facebook)
- [x] Browser automation (Playwright: navigate, click, fill, screenshot)
- [x] System info, app opener, persistent memory
- [x] SQLite conversation history + auto compaction
- [ ] Spotify integration
- [ ] Wake-word activation
- [ ] Web UI

## License

MIT License © 2025 Gandodi Praneeth Kumar