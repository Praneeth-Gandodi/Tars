# Installing & Running TARS — Every Device, No Docker

> ## ℹ️ Branch: use `dev`
>
> The installers and this guide live on the **`dev`** branch, not GitHub's
> default `main`. The one-command installers below **clone the project, switch
> to `dev`, and stay on it automatically** — you don't have to touch git at all.
> If you download the **zip** instead, pick the `dev` branch in the GitHub
> branch dropdown before downloading.

TARS is a **terminal-based voice AI assistant** (Groq-powered, with 30+ built-in
tools). The bundled Docker image is too large to share, so this guide covers the
**native install** — a plain Python setup that runs on **Windows, macOS, Linux
and WSL2**, with no containers.

> **TL;DR** — one copy-paste per platform:
>
> | Platform | Command |
> |---|---|
> | Windows (PowerShell) | `irm https://raw.githubusercontent.com/Praneeth-Gandodi/Tars/dev/install.ps1 \| iex` |
> | macOS (Terminal) | `curl -fsSL https://raw.githubusercontent.com/Praneeth-Gandodi/Tars/dev/install.sh \| bash` |
> | Linux / WSL2 (bash) | `curl -fsSL https://raw.githubusercontent.com/Praneeth-Gandodi/Tars/dev/install.sh \| bash` |
>
> Then paste your Groq API key and run `python tars.py`.

---

## 0. What you need (any device)

| Requirement | Why |
|---|---|
| **Internet connection** | first install downloads packages + speech model |
| **A free Groq API key** | the actual "brain" — get one at <https://console.groq.com/keys> |
| **Python 3.12 / 3.13** | **only** for the manual setup below — the installers install it for you |

The installers handle **everything else**: Python, system libraries (ffmpeg,
audio, browser deps), a virtual environment, all Python packages, Chromium, your
API key, and the speech model.

Voice modes additionally need a **microphone** and **speakers** — every modern
laptop, desktop and phone already has them.

---

## 1. One-command installation (recommended)

Paste **one line** into your terminal. That's it — the installer:

1. Clones TARS (auto-switches to the **`dev` branch**) into a `Tars` folder.
2. **Installs Python 3.12 itself** if it isn't installed yet — Homebrew on macOS,
   `apt` (+deadsnakes PPA when needed) on Debian/Ubuntu, `dnf`/`pacman`
   elsewhere, standalone via `uv` as a last resort. Too-new system Pythons
   (e.g. 3.14) are avoided, since the audio deps are validated on 3.12/3.13.
3. Installs the **system libraries** TARS needs (ffmpeg, audio, browser deps) —
   including the venv package matching its Python, so `python -m venv` never
   fails with "ensurepip is not available".
4. Creates an isolated Python **virtual environment** (`.venv`).
5. Installs **all Python dependencies** — GPU-aware: full CUDA PyTorch when an
   NVIDIA GPU is detected, tiny CPU-only PyTorch otherwise (skips ~1.5GB of
   NVIDIA wheels). Re-running later swaps the build automatically if your
   hardware situation changed.
6. Installs the **Chromium browser** for the browser-automation tools.
7. Creates `.env` and asks for your **Groq API key**.
8. **Pre-warms the speech-to-text model** so voice mode is instant.

It is **idempotent** — run it again any time to repair or upgrade; it simply
picks up where it left off.

### Windows

Open **PowerShell** (Start → type `powershell`) and paste:

```powershell
Set-ExecutionPolicy -Scope Process Bypass   # once, per window — allows the install
irm https://raw.githubusercontent.com/Praneeth-Gandodi/Tars/dev/install.ps1 | iex
```

That's it. The script installs Python if needed (via winget), clones TARS into
`.\Tars`, sets up everything, and asks for your API key.

> **No PowerShell / different machine?** Use the zip route instead:
> GitHub → `Code` → **Download ZIP** (pick the **`dev`** branch first), extract,
> and run `.\install.ps1` from inside the folder.

### macOS

Open **Terminal** and paste:

```bash
curl -fsSL https://raw.githubusercontent.com/Praneeth-Gandodi/Tars/dev/install.sh | bash
```

That's it. The script installs **Homebrew** (if missing), then **Python 3.12**
via Homebrew, then `ffmpeg` + `portaudio`, then the rest. It puts TARS in
`~/Tars` (wherever you ran the command).

> No Homebrew yet? The script installs it for you — nothing manual.

### Linux (Debian / Ubuntu / Fedora / Arch, incl. WSL2)

Open a terminal and paste:

```bash
curl -fsSL https://raw.githubusercontent.com/Praneeth-Gandodi/Tars/dev/install.sh | bash
```

That's it. The script detects your package manager (`apt` / `dnf` / `pacman`),
installs Python 3.12 if needed, and installs the right libraries (ffmpeg,
PortAudio, OpenMP, audio runtime). On **WSL2** the same command works — see the
WSL2 audio section below to enable voice.

> **NVIDIA GPU?** The installer checks with `nvidia-smi` (card + drivers must
> both be present). GPU found → full CUDA PyTorch and GPU-accelerated
> transcription. No GPU → CPU-only PyTorch (~1.5GB of CUDA downloads skipped)
> and CPU transcription. macOS is always CPU (no CUDA on Mac). TARS picks the
> right mode automatically at runtime — nothing to configure. A card *without*
> drivers counts as "no GPU" (CUDA can't run anyway) — install drivers from
> https://www.nvidia.com/drivers and re-run the installer to switch builds.

---

## 2. Manual setup (if you prefer to do it step by step)

> The one-command installers do all of this for you **including installing
> Python**. This manual route assumes Python 3.12/3.13 is already on your
> machine (https://www.python.org/downloads/).

```bash
# 1. Get the code (dev branch — the install files live there)
git clone https://github.com/Praneeth-Gandodi/Tars.git
cd Tars
git checkout dev

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

If you used a one-command installer, TARS lives in a `Tars` folder where you ran
it (e.g. `~/Tars` or `C:\Users\you\Tars`). Step into it and run:

```bash
cd Tars
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

# Now install TARS natively (one command, from your home folder):
cd ~
curl -fsSL https://raw.githubusercontent.com/Praneeth-Gandodi/Tars/dev/install.sh | bash
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
| `python` is not recognized (Windows, manual setup) | The installers install Python automatically. For manual setup: install Python 3.12 with **Add to PATH** ticked, open a **new** terminal. |
| `ensurepip is not available` / venv creation fails (Debian/Ubuntu) | Handled automatically — the installer puts in the venv package matching its Python (`python3.X-venv`) and retries via `uv` if needed. Manual setup: `sudo apt install -y python3.X-venv` (X = your Python's minor version). |
| Installer pulled huge `nvidia-*`/CUDA packages but I have no GPU | Re-run the installer — it detects GPUs and swaps CUDA PyTorch for the CPU-only build automatically (reclaims ~1.5GB). |
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
