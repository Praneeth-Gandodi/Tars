# Installing & Running TARS — Every Device, No Docker

> ## ⚠️ Use the `dev` branch
>
> The installers, `INSTALLATION.md` and the cross-platform setup live on the
> **`dev`** branch. The default GitHub branch (`main`) does **not** have them,
> so **switch to `dev` right after cloning** before following any step below:
>
> ```bash
> git clone https://github.com/Praneeth-Gandodi/Tars.git
> cd Tars
> git checkout dev        # ← do this first
> ```
>
> (If you download the **zip** instead, pick the `dev` branch in the GitHub
> branch dropdown before downloading.)

TARS is a **terminal-based voice AI assistant** (Groq-powered, with 30+ built-in
tools). The bundled Docker image is too large to share, so this guide covers the
**native install** — a plain Python setup that runs on **Windows, macOS, Linux
and WSL2**, with no containers.

> **TL;DR** — one command per platform:
>
> | Platform | Command |
> |---|---|
> | Windows | `.\install.ps1` |
> | macOS | `./install.sh` |
> | Linux / WSL2 | `./install.sh` |
>
> Then paste your Groq API key and run `python tars.py`.

---

## 0. What you need (any device)

| Requirement | Why |
|---|---|
| **Python 3.12** (3.13 also fine) | TARS and its deps target 3.12 |
| **Internet connection** | first install downloads packages + speech model |
| **A free Groq API key** | the actual "brain" — get one at <https://console.groq.com/keys> |
| **git** | to clone the repo (or just download the zip) |

Voice modes additionally need a **microphone** and **speakers** — every modern
laptop, desktop and phone already has them.

---

## 1. One-command installation (recommended)

The installers below do **everything** for you, on any device where they're run:

1. Detect / guide you to Python 3.12.
2. Install the **system libraries** TARS needs (ffmpeg, audio, browser deps).
3. Create an isolated Python **virtual environment** (`.venv`).
4. Install **all Python dependencies**.
5. Install the **Chromium browser** for the browser-automation tools.
6. Create `.env` and ask for your **Groq API key**.
7. **Pre-warm the speech-to-text model** so voice mode is instant.

They are idempotent — run them again any time to repair or upgrade, and they
simply pick up where they left off.

### Windows

Open **PowerShell** (Start → type `powershell`) and run:

```powershell
# (one time) allow local scripts for just this window
Set-ExecutionPolicy -Scope Process Bypass

cd C:\Users\you\Projects      # or any folder you like
git clone https://github.com/Praneeth-Gandodi/Tars.git
cd Tars
.\install.ps1
```

If you don't have git installed, grab the project as a **zip** (GitHub →
`Code` → `Download ZIP`), extract it, and run `.\install.ps1` inside the folder.

### macOS

Open **Terminal** and run:

```bash
cd ~/Projects && mkdir -p Projects && cd Projects
git clone https://github.com/Praneeth-Gandodi/Tars.git
cd Tars
chmod +x install.sh
./install.sh
```

The script uses **Homebrew** to install `ffmpeg` and `portaudio`. If Homebrew
isn't installed, it tells you how (or run `./install.sh --no-system`).

### Linux (Debian / Ubuntu / Fedora / Arch, incl. WSL2)

From a terminal:

```bash
cd ~
git clone https://github.com/Praneeth-Gandodi/Tars.git
cd Tars
chmod +x install.sh
./install.sh
```

The script detects your package manager (`apt` / `dnf` / `pacman`) and installs
the right libraries (ffmpeg, PortAudio, OpenMP, audio runtime). On **WSL2** the
same `install.sh` works — see the WSL2 audio section below to enable voice.

---

## 2. Manual setup (if you prefer to do it step by step)

The installer runs these exact steps. Useful if a step fails and you want to
troubleshoot it individually.

```bash
# 1. Get the code
git clone https://github.com/Praneeth-Gandodi/Tars.git
cd Tars

# 2. Virtual environment
python -m venv .venv
#   Windows:
.venv\Scripts\activate
#   macOS / Linux:
source .venv/bin/activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Browser automation (optional, only for browser tools)
playwright install chromium          # Windows/macOS
python -m playwright install --with-deps chromium   # Linux (installs system deps)

# 5. Configuration
cp .env.example .env                 # then paste your Groq key into .env
```

---

## 3. Configuration

TARS reads two files on startup:

### `.env` (secrets / model)

| Variable | Example | Notes |
|---|---|---|
| `groq_api` | `gsk_xxxxxxxx` | **Required.** From <https://console.groq.com/keys> |
| `model` | `openai/gpt-oss-120b` | Any Groq model ID |

If `.env` is missing `groq_api`, TARS **asks you on first launch** and writes it
for you — so you can even skip copying `.env.example`.

### `settings.toml` (behavior)

| Setting | What it does |
|---|---|
| `display_function_response` | `1` show tool + response · `2` show tool only · `3` hide |
| `auto_summarize` / `summarize_interval` | auto-compact the chat to save tokens every N turns |
| `default_mode` | 1 = Text, 2 = Voice→Voice, 3 = Voice→Text |
| `web_browser_exe_path` | optional browser path for the "open in browser" tool |

---

## 4. Running TARS

```bash
python tars.py
#   or, if you didn't activate the venv:
#   Windows:   .venv\Scripts\python.exe tars.py
#   macOS/Lin: .venv/bin/python tars.py
```

You'll get a mode picker:

- **1 — Text → Text**: type, TARS replies. Works everywhere, no audio needed.
- **2 — Voice → Voice**: speak, hear the reply, and interrupt by talking over it.
- **3 — Voice → Text**: speak, read the reply.

### Commands while chatting

| Command | Action |
|---|---|
| `/help` | list commands + all loaded tools |
| `/sessions` | list recent conversations |
| `/resume <id>` | continue an old conversation |
| `/summarize` | compact the current chat now |
| `/clear` | clear the screen |
| `/exit` | quit |

---

## 5. Making voice work on each OS

Voice (STT + TTS) is fully **offline** — speech recognition runs local Whisper,
speech synthesis runs local Piper. Here's what each OS needs to pass audio
through.

### Windows ✅ (simplest)

Nothing extra. Installer arms `ffmpeg` (needed by STT pre-processing and the
video downloader). Make sure `.env` has your key, pick **Voice → Voice**, and
talk. If the mic isn't picked up:

- Windows **Settings → Privacy → Microphone** → *Allow apps to access the mic*.
- Confirm you have a default **input** and **output** device (Control Panel → Sound).

### macOS ✅

The installer's Homebrew step gives you `portaudio` (the backend `sounddevice`
uses). Grant **System Settings → Privacy & Security → Microphone** permission to
your Terminal app, then pick **Voice → Voice**.

### Linux (native / non-WSL) ✅

Make sure you installed the audio packages (`libportaudio2`, `libpulse0`,
`libasound2-plugins`) — `install.sh` does this. Ensure a working PulseAudio or
PipeWire setup (`pactl info` should show a default sink/source), grant your
terminal mic access, then run.

### WSL2 🎧 (Windows, full voice via WSLg)

WSL2's built-in **WSLg** bridges your Windows mic/speakers into Linux, so Docker
isn't needed at all — just install TARS natively in the distro:

```bash
# inside your WSL2 Ubuntu terminal
wsl --update          # ensure WSLg is present
wsl --shutdown        # then reopen the terminal

# Confirm the audio bridge exists:
ls /mnt/wslg/PulseServer      # must exist

# Now install TARS natively:
cd ~
git clone https://github.com/Praneeth-Gandodi/Tars.git
cd Tars && chmod +x install.sh && ./install.sh
```

To **use** audio from inside the distro, WSLg usually sets `PULSE_SERVER`
automatically. If you hear nothing, set it explicitly, and check with `pactl`:

```bash
export PULSE_SERVER=unix:/mnt/wslg/PulseServer
pactl list sinks short     # your Windows speakers
pactl list sources short   # your Windows microphone
```

> Audio can only be reached from the **distro running the app**, and your
> Windows mic must be allowed (Settings → Privacy → Microphone).

### No audio device at all (headless server / CI) 💻

Text mode and every tool work fine with zero audio hardware. Pick **Text →
Text** at the start.

---

## 6. First voice run: what downloads (and where it's cached)

- **Piper TTS voice** (`en_US-norman-medium.onnx`, ~60 MB) is **bundled in the
  repo** under `assets/tts_models/` — nothing to download; it's already there.
- **Whisper STT model** (`small.en`, ~250 MB) is downloaded by the installer's
  pre-warm step and cached once. Later runs reuse the cache — no re-download.

If you skipped the pre-warm (`--no-voice` / `-NoVoice`), the model downloads
automatically the first time you enter a voice mode. Job done.

---

## 7. Troubleshooting

| Symptom | Fix |
|---|---|
| `python` is not recognized (Windows) | Reinstall Python 3.12 and tick **Add to PATH**; open a **new** terminal. |
| pip errors about `markrender` | It's installed from GitHub — you need git + network: `pip install -r requirements.txt` again. |
| `AppOpener` / apps tool fails on Linux | By design — the app-opener tool is **Windows-only**. Other tools are unaffected. |
| Voice picks up nothing | Check `.env` key; grant mic permission; ensure a default mic set. On Linux check `pactl list sources`. |
| Browser tools fail | Run `playwright install chromium` (Linux: with `--with-deps`). Text + other tools still work without it. |
| `libgomp.so.1: cannot open` (Linux) | Install `libgomp1` (`sudo apt install -y libgomp1`). |
| Video download fails on `ffmpeg` | Install / add `ffmpeg` to PATH (needed for merging audio+video). |
| `SystemExit` on Linux at startup | Depends on an old app_open import — update to the latest commit (`git pull`). |
| Slow first voice run | That's the whisper model caching. It's a one-time ~250 MB download. |
| GPU? | TARS runs on CPU by default and works fine. No CUDA needed. |

---

## 8. Uninstalling

Simply delete the project folder — TARS is self-contained in it. Optional
leftovers:

- The whisper model cache (per-OS):
  - Windows: `%USERPROFILE%\.cache\huggingface`
  - macOS/Linux: `~/.cache/huggingface`
- (Linux) the packages the installer added, e.g. `sudo apt remove ffmpeg portaudio19-dev libgomp1`.

---

## 9. Quick reference

```
install.ps1        Windows installer (PowerShell)
install.sh         macOS / Linux / WSL2 installer (Bash)
INSTALLATION.md    this guide
requirements.txt   Python dependencies
tars.py            entry point: pick a mode, then chat
main.py            LLM orchestration + tool calling
supporter.py       tool registry
tools/             individual tools (web, wiki, files, browser, ...)
assets/tts_models/ Piper TTS voice (bundled)
settings.toml      behavior / tool-display options
.env.example       copy to .env and fill in your Groq key
```

**Run it:** `python tars.py` → pick **Text → Text** (or **Voice → Voice**) → say
`/help` to see every command and tool.
