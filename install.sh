#!/usr/bin/env bash
#
#============================================================================
#  TARS - Voice AI Assistant
#  Installer for macOS, Linux and WSL2 (Bash)
#============================================================================
#  One command, any Unix system:
#
#      curl -fsSL https://raw.githubusercontent.com/Praneeth-Gandodi/Tars/dev/install.sh | bash
#
#  The script does EVERYTHING for you:
#    - Installs Python 3.12/3.13 itself if it isn't installed yet
#    - Installs the system libraries TARS needs (ffmpeg, audio, browser deps)
#    - Clones the project (dev branch) into ./Tars and keeps you on 'dev'
#    - Creates a virtual environment + installs all Python dependencies
#    - Installs the Playwright / Chromium browser (browser automation)
#    - Sets up .env with your Groq API key
#    - Pre-warms the speech-to-text model for instant voice
#
#  You can also run it from inside a Tars folder (it detects and reuses it),
#  and it is idempotent: re-run any time to repair or upgrade.
#
#  Flags:
#      --no-voice        skip STT-model prewarming (faster)
#      --skip-browser    skip the Playwright browser install
#      --no-system       skip system-package install (you handle it)
#      --repo-url=URL    clone from a different repo URL
#============================================================================

set -euo pipefail

REPO_URL="https://github.com/Praneeth-Gandodi/Tars.git"
DO_VOICE=1
DO_BROWSER=1
DO_SYSTEM=1

for arg in "$@"; do
    case "$arg" in
        --no-voice)      DO_VOICE=0 ;;
        --skip-browser)  DO_BROWSER=0 ;;
        --no-system)     DO_SYSTEM=0 ;;
        --repo-url=*)    REPO_URL="${arg#*=}" ;;
        *) echo "Unknown argument: $arg" >&2; exit 1 ;;
    esac
done

step() { printf '\n\033[1;36m=== %s ===\033[0m\n' "$*"; }
ok()   { printf '  \033[1;32m[OK]\033[0m %s\n' "$*"; }
warn() { printf '  \033[1;33m[!!]\033[0m %s\n' "$*"; }

command_exists() { command -v "$1" >/dev/null 2>&1; }
python_ok() { "$1" -c 'import sys; sys.exit(0 if sys.version_info >= (3,12) else 1)' 2>/dev/null; }

echo ""
echo "====================================================================="
echo "  TARS  -  Voice AI Assistant  (macOS / Linux / WSL2 installer)"
echo "====================================================================="

DETECT_OS="$(uname -s)"

# ------------------------------------------------------------------
# 1. Get the project (clone into ./Tars if we're not already inside a
#    checkout — this is what makes the one-line `curl | bash` work).
# ------------------------------------------------------------------
step "Preparing the TARS project"
if [ -f "./tars.py" ]; then
    ok "Running from an existing TARS folder ($(pwd))."
elif command_exists git; then
    if [ ! -d "./Tars" ]; then
        git clone "$REPO_URL" Tars
        ok "Cloned TARS."
    else
        ok "Tars folder already exists - reusing it."
    fi
    cd Tars
    # Fresh clones land on the default branch; the install files live on 'dev'.
    git checkout dev 2>/dev/null || { git fetch origin dev && git checkout dev; }
    ok "On the 'dev' branch."
else
    # No git yet (system packages install it later) - grab the dev tarball so
    # the rest of the install can proceed anyway.
    if [ ! -d "./Tars" ]; then
        curl -fsSL "${REPO_URL%.git}/archive/refs/heads/dev.tar.gz" | tar -xz
        mv "Tars-dev" Tars
        ok "Downloaded TARS (dev branch, no git needed)."
    fi
    cd Tars
fi

# ------------------------------------------------------------------
# 2. Make sure Python 3.12/3.13 exists — install it if it doesn't.
# ------------------------------------------------------------------
step "Ensuring Python 3.12+"
PYTHON=""
for c in python3 python3.12 python3.13; do
    if command_exists "$c" && python_ok "$c"; then
        PYTHON="$c"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    warn "No usable Python 3.12/3.13 found - installing one for you."
    if [ "$DETECT_OS" = "Darwin" ]; then
        # macOS -> Homebrew (installed first if needed)
        if ! command_exists brew; then
            echo "  Installing Homebrew (needed for Python + audio libraries)..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        # Put brew's bin dir on PATH for this session (Apple Silicon vs Intel).
        if [ -x /opt/homebrew/bin/brew ]; then
            eval "$(/opt/homebrew/bin/brew shellenv)"
        elif [ -x /usr/local/bin/brew ]; then
            eval "$(/usr/local/bin/brew shellenv)"
        elif command_exists brew; then
            eval "$(brew shellenv)"
        else
            warn "Homebrew could not be set up - install it from https://brew.sh and re-run."
            exit 1
        fi
        brew install python@3.12
        PYTHON="$(brew --prefix)/bin/python3.12"

    elif command_exists apt-get; then
        # Debian / Ubuntu / WSL2-Ubuntu
        sudo apt-get update
        if ! sudo apt-get install -y python3.12 python3.12-venv; then
            # Older Ubuntu/Debian don't ship 3.12 -> use the deadsnakes PPA.
            warn "python3.12 isn't in this distro's repos - adding the deadsnakes PPA."
            command_exists add-apt-repository || sudo apt-get install -y software-properties-common
            sudo add-apt-repository -y ppa:deadsnakes/ppa
            sudo apt-get update
            sudo apt-get install -y python3.12 python3.12-venv
        fi
        PYTHON=python3.12

    elif command_exists dnf; then
        # Fedora / RHEL
        sudo dnf install -y python3.12 python3.12-pip || sudo dnf install -y python3.13 python3.13-pip
        PYTHON="$(command -v python3.12 || command -v python3.13 || echo python3)"

    elif command_exists pacman; then
        # Arch / Manjaro
        sudo pacman -Sy --noconfirm python
        PYTHON=python3

    else
        # Universal fallback: uv (installs standalone Pythons, no root needed).
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.local/bin:$PATH"
        uv python install 3.12
        PYTHON="$(uv python find 3.12)"
    fi
fi

if [ -n "$PYTHON" ] && python_ok "$PYTHON"; then
    ok "Using Python: $PYTHON ($("$PYTHON" --version 2>&1))"
else
    warn "Could not install Python 3.12+ automatically."
    warn "Install it manually from https://www.python.org/downloads/ and re-run."
    exit 1
fi

# ------------------------------------------------------------------
# 3. Install system libraries (best-effort; requires sudo on Linux).
# ------------------------------------------------------------------
if [ "$DO_SYSTEM" -eq 1 ]; then
    step "Installing system libraries TARS needs"

    if [ "$DETECT_OS" = "Darwin" ]; then
        # Homebrew is guaranteed present from the Python step above.
        brew update || true
        # ffmpeg: STT + video downloader. portaudio: audio backend (sounddevice).
        brew install ffmpeg portaudio pkg-config
        ok "Installed ffmpeg + portaudio via Homebrew."

    elif command_exists apt-get; then
        # Debian / Ubuntu / WSL2-Ubuntu
        sudo apt-get update
        sudo apt-get install -y --no-install-recommends \
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
[ -x "$PY" ] || { warn "venv Python not found (falling back to system)"; PY="$PYTHON"; }

# ------------------------------------------------------------------
# 5. Upgrade pip and install Python dependencies
# ------------------------------------------------------------------
step "Installing Python dependencies (this may take a few minutes)"
"$PY" -m pip install --upgrade pip
"$PY" -m pip install -r requirements.txt
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
echo "      cd $(pwd)"
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