# Running TARS in Docker on **Windows via WSL2** (with voice!)

TARS is fully bundled in a Docker image (Python deps, Piper TTS voice, whisper STT
model, headless Chromium for browser tools) — **nothing downloads at runtime**.
The only catch: **microphone and speaker in a container only work on Linux**, and
on Windows that means going through **WSL2**, because Docker Desktop containers can't
see your audio devices.

There are two ways to run the image on Windows:

- **Option A (recommended):** install Docker **inside WSL2** and pass WSLg's PulseAudio
  socket into the container → **full voice mode works** (talk + hear + interrupt).
- **Option B:** keep using Docker Desktop → **text mode only** (voice has no audio path).

---

## Option A — Docker Engine inside WSL2 + WSLg audio (full voice)

WSL2 ships **WSLg**, whose built-in PulseAudio server bridges the **Windows
microphone and speakers** in and out of Linux. We mount that server's socket into
the container so TARS can use real audio.

### Step 1 — Update WSL and open a shell

In PowerShell:

```powershell
wsl --update
wsl --shutdown
wsl --install -d Ubuntu-24.04    # or your distro of choice
```

Check WSLg is present after opening Ubuntu:

```bash
ls /mnt/wslg/PulseServer   # must exist — this is the audio bridge
wsl --version
```

> If `/mnt/wslg` is missing, run `wsl --update`, restart, and re-check.

### Step 2 — Install Docker inside the WSL2 distro

Inside the Ubuntu terminal (not PowerShell):

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker "$USER"     # lets you run docker without sudo
newgrp docker                       # apply group now (or log out and back in)
sudo service docker start           # or: sudo systemctl enable --now docker
docker --version                    # verify
```

> Docker Desktop is **not** needed for Option A — this is a separate Docker Engine
> living inside WSL2.

### Step 3 — Move the project into the distro and build

Building from `/mnt/c/...` is slow (DrvFs), so copy the folder to your Linux home first.
Your Windows project is visible inside WSL at `/mnt/c/...`:

```bash
cp -r "/mnt/c/Users/<YOUR_WINDOWS_USER>/Projects/Tars" ~/Tars
cd ~/Tars
docker build -t tars .
```

> *Your `.env` API key copied along with the folder, but `.dockerignore` keeps it
> out of the image — you'll mount it at run time (next step).*

### Step 4 — Run the container with audio + your key

```bash
docker run -it --rm \
  --name tars \
  -v /mnt/wslg/PulseServer:/mnt/wslg/PulseServer \
  -e PULSE_SERVER=unix:/mnt/wslg/PulseServer \
  -v ~/Tars/.env:/Tars/.env:ro \
  --shm-size=1g \
  tars
```

| Flag | Why |
|---|---|
| `-v /mnt/wslg/PulseServer:/mnt/wslg/PulseServer` | gives the container the WSLg audio socket (speaker + mic) |
| `-e PULSE_SERVER=unix:/mnt/wslg/PulseServer` | tells Audio/ALSA to use that socket |
| `-v ~/Tars/.env:/Tars/.env:ro` | provides the Groq API key (`.env` is intentionally not baked into the image) |
| `--shm-size=1g` | required by Chromium (browser automation tools) |

If you'd rather pass the key as an env var instead of mounting the file:

```bash
docker run -it --rm -v /mnt/wslg/PulseServer:/mnt/wslg/PulseServer \
  -e PULSE_SERVER=unix:/mnt/wslg/PulseServer \
  -e groq_api="sk-..." -e model="openai/gpt-oss-120b" \
  --shm-size=1g tars
```

### Step 5 — Sanity-check audio before talking

In a second Ubuntu terminal:

```bash
docker exec -it tars bash
pactl list sinks short      # a sink = your Windows speaker
pactl list sources short    # a source = your Windows microphone
exit
```

Both should list at least one device. If they're empty, see Troubleshooting below.

Then just use it — choose **Option 2 (Voice → Voice)** in the menu:

```bash
python tars.py
```

TARS is interruptible: start speaking and the TTS reply cuts off instantly.

---

## Option B — Docker Desktop on Windows (text mode only)

If you want to stick with Docker Desktop:

```powershell
docker build -t tars .
docker run -it --rm -e groq_api="sk-..." -e model="openai/gpt-oss-120b" tars
```

This works great for **text mode** and all tools. Voice won't work here because
Docker Desktop's containers run in a separate VM that has no audio device or
WSLg socket — that's exactly why Option A exists.

---

## Fallback: no Docker, run natively in WSL2

If the container ever fights you, the simplest path is to run TARS directly in the
distro — WSLg gives native apps audio with zero plumbing:

```bash
sudo apt update && sudo apt install -y python3.12 python3.12-venv ffmpeg
cd ~/Tars
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
pip install piper-tts
cp .env.example .env            # paste your key
python tars.py
```

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `pactl list sinks` is empty in the container | WSLg not running: `wsl --update`, `wsl --shutdown`, reopen Ubuntu; confirm `/mnt/wslg/PulseServer` exists **on the distro** before `docker run` |
| No sound heard | Windows volume + app volume; in WSL `pulseaudio -k` (restarts the WSLg server); some drivers need `wsl --shutdown` + restart after Windows audio changes |
| Mic not being heard | Windows **Settings → Privacy → Microphone** → allow apps; WSLg forwards the default Windows mic |
| Chromium / browser tool crashes | add/raise `--shm-size=1g` |
| `docker: permission denied` | `sudo usermod -aG docker $USER` then log out/in (or use `newgrp docker`) |
| Build is very slow | you built from `/mnt/c/...`; copy to `~/Tars` first |
| First STT run still downloads | image was built before the whisper layer finished; rebuild (`docker build -t tars .`) or ensure you're on the latest image |
| API key error inside container | `.env` isn't baked in — mount it (`-v ~/Tars/.env:/Tars/.env:ro`) or pass `-e groq_api=...` |