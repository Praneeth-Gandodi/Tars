#!/usr/bin/env bash
#
#============================================================================
#  TARS - Voice AI Assistant
#  Installer for macOS, Linux and WSL2 (Bash)
#============================================================================
#  - Creates a Python 3.12 virtual environment
#  - Installs the system libraries TARS needs (ffmpeg, audio, etc.)
#  - Installs Python dependencies
#  - Installs the Playwright / Chromium browser (browser automation)
#  - Sets up .env with your Groq API key
#  - (Optional) pre-warms the speech-to-text model for instant voice
#
#  Usage:
#      chmod +x install.sh
#      ./install.sh
#
#  Flags:
#      ./install.sh --no-voice        skip STT-model prewarming (faster)
#      ./install.sh --repo-url URL    clone from a different repo URL
#      ./install.sh --skip-browser    skip the Playwright browser install
#      ./install.sh --no-system       skip system-package install (you handle it)
#============================================================================

set -euo pipefail

REPO_URL="https://github.com/Praneeth-Gandodi/Tars.git"
DO_VOICE=1
DO_BROWSER=1
DO_SYSTEM=1

for arg in "$@"; do
    case "$arg" in
        --no-voice)   DO_VOICE=0 ;;
        --skip-browser) DO_BROWSER=0 ;;
        --no-system)  DO_SYSTEM=0 ;;
        --repo-url=*) REPO_URL="${arg#*=}" ;;
        *) echo "Unknown argument: $arg" >&2; exit 1 ;;
    esac
done

step() { printf '\n\033[1;36m=== %s ===\033[0m\n' "$*"; }
ok()   { printf '  \033[1;32m[OK]\033[0m %s\n' "$*"; }
warn() { printf '  \033[1;33m[!!]\033[0m %s\n' "$*"; }

command_exists() { command -v "$1" >/dev/null 2>&1; }

echo ""
echo "====================================================================="
echo "  TARS  -  Voice AI Assistant  (macOS / Linux / WSL2 installer)"
echo "====================================================================="

DETECT_OS="$(uname -s)"

# ------------------------------------------------------------------
# 1. Find Python 3.12+ (will use the first 3.12/3.13 it finds)
# ------------------------------------------------------------------
step "Looking for Python 3.12+"
PYTHON=""
for c in python3.12 python3.13 python3; do
    if command_exists "$c"; then
        ver="$("$c" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || true)"
        case "$ver" in
            3.12|3.13) PYTHON="$c"; break ;;
        esac
    fi
done

if [ -z "$PYTHON" ]; then
    warn "Python 3.12/3.13 was not found."
    if [ "$DETECT_OS" = "Darwin" ]; then
        echo ""
        echo "  Install Python 3.12 with Homebrew:"
        echo "      brew install python@3.12"
        echo "  Then re-run this script."
    else
        echo ""
        echo "  Install Python 3.12 with your package manager, e.g.:"
        echo "      sudo apt install -y python3.12 python3.12-venv   # Debian/Ubuntu"
        echo "      sudo dnf install -y python3.12                    # Fedora"
        echo "      sudo pacman -S python                             # Arch"
        echo "  or from https://www.python.org/downloads/"
        echo "  Then re-run this script."
    fi
    exit 1
fi
ok "Using Python: $PYTHON ($("$PYTHON" --version 2>&1))"

# ------------------------------------------------------------------
# 2. Install system libraries (best-effort; requires sudo for Linux)
# ------------------------------------------------------------------
if [ "$DO_SYSTEM" -eq 1 ]; then
    step "Installing system libraries TARS needs"

    if [ "$DETECT_OS" = "Darwin" ]; then
        # macOS -> Homebrew
        if ! command_exists brew; then
            warn "Homebrew not found - skipping system packages."
            warn "Install it from https://brew.sh then re-run, or use --no-system."
        else
            brew update
            # ffmpeg is needed by STT and the video downloader.
            # portaudio is the audio backend used by sounddevice.
            brew install ffmpeg portaudio pkg-config
            ok "Installed ffmpeg + portaudio via Homebrew."
        fi

    elif command_exists apt-get; then
        # Debian / Ubuntu / WSL2-Ubuntu
        sudo apt-get update
        sudo apt-get install -y --no-install-recommends \
            python3-venv \
            ffmpeg \
            git \
            build-essential \
            portaudio19-dev \
            libgomp1 \
            libportaudio2 \
            libpulse0 \
            libasound2-plugins \
            pulseaudio-utils
        ok "Installed apt packages (ffmpeg, portaudio, audio runtime)."

    elif command_exists dnf; then
        sudo dnf groupinstall -y "Development Tools"
        sudo dnf install -y ffmpeg portaudio-devel libgomp python3-pip
        ok "Installed dnf packages (ffmpeg, portaudio, libgomp)."

    elif command_exists pacman; then
        sudo pacman -Sy --noconfirm ffmpeg portaudio base-devel gcc-ada
        ok "Installed pacman packages (ffmpeg, portaudio)."

    else
        warn "Could not detect your package manager."
        warn "Install ffmpeg + an audio library (portaudio) manually, or rerun with --no-system."
    fi
fi

# ------------------------------------------------------------------
# 3. Clone or reuse the project
# ------------------------------------------------------------------
step "Preparing the project folder"
if [ ! -f "./tars.py" ]; then
    if ! command_exists git; then
        warn "git was not found - install it and re-run, or copy the project here manually."
        exit 1
    fi
    git clone "$REPO_URL" .
    ok "Cloned TARS from $REPO_URL"
else
    ok "tars.py already present in this folder - reusing it."
fi

# ------------------------------------------------------------------
# 4. Create the virtual environment
# ------------------------------------------------------------------
step "Creating a virtual environment"
if [ ! -d "./.venv" ]; then
    "$PYTHON" -m venv .venv
    ok "Virtual environment created at .venv"
else
    ok "Virtual environment already exists."
fi

PY=".venv/bin/python"
PIP="$PY -m pip"
[ -x "$PY" ] || { warn "venv Python not found (falling back to system)"; PY="$PYTHON"; PIP="$PYTHON -m pip"; }

# ------------------------------------------------------------------
# 5. Upgrade pip and install Python dependencies
# ------------------------------------------------------------------
step "Installing Python dependencies (this may take a few minutes)"
"$PIP" install --upgrade pip
"$PIP" install -r requirements.txt
ok "Python dependencies installed."

# ------------------------------------------------------------------
# 6. Install the Playwright browser (browser automation tools)
# ------------------------------------------------------------------
if [ "$DO_BROWSER" -eq 1 ]; then
    step "Installing Playwright Chromium + system dependencies"
    "$PY" -m playwright install --with-deps chromium || {
        warn "Chromium install had issues. Text + most tools still work."
        warn "Retry later with:  .venv/bin/python -m playwright install chromium"
    }
    ok "Chromium installed for browser tools."
fi

# ------------------------------------------------------------------
# 7. Set up .env with the Groq API key
# ------------------------------------------------------------------
step "Configuring .env"
if [ ! -f "./.env" ]; then
    cp .env.example .env
    ok "Created .env from .env.example"
fi

if grep -q "your_groq_api_key_here" .env; then
    printf '  Enter your free Groq API key (https://console.groq.com/keys): '
    read -r KEY
    if [ -n "$KEY" ] && [ "$KEY" != "your_groq_api_key_here" ]; then
        sed -i.bak "s/your_groq_api_key_here/$KEY/" .env && rm -f .env.bak
        ok "API key saved to .env"
    else
        warn "No key entered - open .env later and paste it into the groq_api= line."
    fi
else
    ok ".env already has a key configured."
fi

# ------------------------------------------------------------------
# 8. (Optional) Pre-warm the speech-to-text model for instant voice
# ------------------------------------------------------------------
if [ "$DO_VOICE" -eq 1 ]; then
    step "Pre-warming the voice recognition model (~250MB, one-time)"
    echo "  This makes first voice use instant. Skip with: --no-voice"
    "$PY" -c "from faster_whisper import WhisperModel; WhisperModel('small.en', device='cpu', compute_type='int8')" \
        && ok "Whisper STT model cached." \
        || warn "Model pre-warm failed - TARS downloads it on first voice use instead."
fi

# ------------------------------------------------------------------
# 9. Summary
# ------------------------------------------------------------------
echo ""
echo "====================================================================="
echo "  TARS installed!"
echo "====================================================================="
echo ""
echo "  Start TARS:"
echo "      .venv/bin/python tars.py"
echo "    or first:   source .venv/bin/activate"
echo ""
echo "  Text mode works right away."
echo "  Voice mode needs a working microphone + speakers."
if [ "$DETECT_OS" != "Darwin" ]; then
    echo "  (On WSL2 use the WSL2 section of INSTALLATION.md for audio.)"
fi
echo ""
echo "  Need help? See INSTALLATION.md"
echo "====================================================================="
