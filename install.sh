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
#    - Installs Python 3.12 itself if it isn't installed yet (Homebrew on
#      macOS; apt + deadsnakes PPA if needed on Debian/Ubuntu; dnf/pacman
#      elsewhere; standalone via uv as a last resort). Too-new system
#      Pythons (e.g. 3.14) are avoided: audio deps are validated on 3.12/3.13.
#    - Installs the venv package matching its Python (fixes "ensurepip is
#      not available" on Debian/Ubuntu) + system libraries (ffmpeg, audio,
#      browser deps)
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

# Bump this whenever installer behavior changes. It prints in the banner so
# pasted logs reveal exactly which script copy ran — raw.githubusercontent.com
# caches for a few minutes, so a re-run right after a fix may use a stale copy.
INSTALLER_REV="2026-09-08e"

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

# True when an NVIDIA GPU is actually usable: card present AND drivers
# installed (nvidia-smi lists it). A card without drivers can't run CUDA
# anyway, so driver presence is the right test — CUDA wheels are only
# useful when torch.cuda can actually use them.
has_nvidia_gpu() {
    command_exists nvidia-smi && nvidia-smi -L 2>/dev/null | grep -qi "GPU"
}

# Installs uv (fast Python manager) if missing — used both to fetch a
# standalone Python 3.12 and as a fallback venv creator. Needs no root.
ensure_uv() {
    command_exists uv && return 0
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    command_exists uv
}

# True when the chosen interpreter is a standalone uv build (ships its own
# headers — no system -dev package needed or wanted).
is_uv_python() {
    case "$PYTHON" in
        *"/uv/python/"*|*".local/share/uv"*) return 0 ;;
    esac
    return 1
}

# Installs Homebrew if missing (macOS) and puts it on this session's PATH
# (handles both Apple Silicon and Intel locations).
ensure_brew() {
    command_exists brew && return 0
    echo "  Installing Homebrew (needed for Python + audio libraries)..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    if [ -x /opt/homebrew/bin/brew ]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
    elif [ -x /usr/local/bin/brew ]; then
        eval "$(/usr/local/bin/brew shellenv)"
    fi
    command_exists brew
}

echo ""
echo "====================================================================="
echo "  TARS  -  Voice AI Assistant  (macOS / Linux / WSL2 installer)"
echo "  installer rev $INSTALLER_REV (https://github.com/Praneeth-Gandodi/Tars/tree/dev)"
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
# 2. Make sure a TARS-compatible Python exists — install 3.12 if not.
#    TARS targets 3.12/3.13 (audio deps like PyAudio, RealtimeSTT and
#    piper-tts are validated there), so a newer system Python (e.g. 3.14)
#    is only ever used as a last resort.
# ------------------------------------------------------------------
step "Ensuring Python 3.12+"
PYTHON=""
PYVER=""
NEWER_PY=""
for c in python3.12 python3.13 python3; do
    if command_exists "$c"; then
        ver="$("$c" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || true)"
        case "$ver" in
            3.12|3.13) PYTHON="$c"; PYVER="$ver"; break ;;
            # Newer than 3.13 (e.g. 3.14): remembered as a fallback only.
            3.1[4-9]|3.[2-9][0-9]) [ -z "$NEWER_PY" ] && NEWER_PY="$c" ;;
        esac
    fi
done

if [ -z "$PYTHON" ]; then
    warn "No Python 3.12/3.13 found - installing Python 3.12 for you."
    if [ "$DETECT_OS" = "Darwin" ]; then
        # macOS -> Homebrew (installed first if needed)
        if ensure_brew && brew install python@3.12; then
            PYTHON="$(brew --prefix)/bin/python3.12"
        fi

    elif command_exists apt-get; then
        # Debian / Ubuntu / WSL2-Ubuntu
        sudo apt-get update
        if sudo apt-get install -y python3.12 python3.12-venv; then
            PYTHON=python3.12
        elif grep -qi '^ID=ubuntu' /etc/os-release 2>/dev/null; then
            # Ubuntu release without 3.12 in its repos -> deadsnakes PPA
            # (Ubuntu-only; Debian goes straight to the uv fallback below).
            warn "python3.12 isn't in this Ubuntu release's repos - adding the deadsnakes PPA."
            command_exists add-apt-repository || sudo apt-get install -y software-properties-common
            if sudo add-apt-repository -y ppa:deadsnakes/ppa \
                && sudo apt-get update \
                && sudo apt-get install -y python3.12 python3.12-venv; then
                PYTHON=python3.12
            fi
        else
            warn "python3.12 isn't in this distro's repos - will try a standalone Python via uv."
        fi

    elif command_exists dnf; then
        # Fedora / RHEL
        if sudo dnf install -y python3.12; then
            PYTHON=python3.12
        elif sudo dnf install -y python3.13; then
            PYTHON=python3.13
        fi

    elif command_exists pacman; then
        # Arch is rolling-release: repos only carry the newest Python, so
        # grab a standalone 3.12 via uv; fall back to the repo Python below.
        if ensure_uv && uv python install 3.12; then
            PYTHON="$(uv python find 3.12)" || PYTHON=""
        elif sudo pacman -Sy --noconfirm python; then
            NEWER_PY=python3
        fi

    else
        # Unknown distro: standalone 3.12 via uv, no root needed.
        if ensure_uv && uv python install 3.12; then
            PYTHON="$(uv python find 3.12)" || PYTHON=""
        fi
    fi

    # Last resort on Linux: standalone 3.12 via uv (covers failed repo installs).
    if [ -z "$PYTHON" ] && [ "$DETECT_OS" != "Darwin" ]; then
        warn "Package-manager install failed - trying standalone Python 3.12 via uv."
        if ensure_uv && uv python install 3.12; then
            PYTHON="$(uv python find 3.12)" || PYTHON=""
        fi
    fi
fi

if [ -z "$PYTHON" ] && [ -n "$NEWER_PY" ]; then
    PYTHON="$NEWER_PY"
    warn "Could not install Python 3.12 - falling back to your system Python."
fi

if [ -z "$PYTHON" ]; then
    warn "Could not install Python 3.12+ automatically."
    warn "Install it manually from https://www.python.org/downloads/ and re-run."
    exit 1
fi

PYVER="$("$PYTHON" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || true)"
case "$PYVER" in
    3.12|3.13)
        ok "Using Python: $PYTHON ($("$PYTHON" --version 2>&1))" ;;
    *)
        warn "Using Python $PYVER ($PYTHON) - TARS targets 3.12/3.13, so some audio packages may fail to install." ;;
esac

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
        # Debian/Ubuntu split venv support per interpreter version: install the
        # venv package matching the Python we are about to use, otherwise
        # `python -m venv` fails with "ensurepip is not available".
        if [ -n "$PYVER" ]; then
            sudo apt-get install -y "python${PYVER}-venv" || \
                warn "Could not install python${PYVER}-venv - venv creation may fail."
            # PyAudio ships no wheel for 3.12+ Linux: it compiles from source
            # and needs the interpreter headers (Python.h).
            if ! is_uv_python; then
                sudo apt-get install -y "python${PYVER}-dev" || \
                    warn "Could not install python${PYVER}-dev - PyAudio build may fail."
            fi
        fi
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
        # Headers for source builds (PyAudio), matching the Python in use.
        if [ -n "$PYVER" ] && ! is_uv_python; then
            sudo dnf install -y "python${PYVER}-devel" || \
                warn "Could not install python${PYVER}-devel - PyAudio build may fail."
        fi
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
    if "$PYTHON" -m venv .venv 2>/dev/null; then
        ok "Virtual environment created at .venv"
    elif ensure_uv && uv venv --python "$PYTHON" .venv; then
        ok "Virtual environment created at .venv (via uv fallback)"
    else
        warn "Could not create the virtual environment."
        echo "  On Debian/Ubuntu this usually means a missing venv package:"
        echo "      sudo apt install -y python${PYVER}-venv"
        echo "  Then re-run this script."
        exit 1
    fi
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

# ------------------------------------------------------------------
# PyTorch: full CUDA build only when an NVIDIA GPU is usable, tiny
# CPU-only build otherwise (saves ~1.5GB of NVIDIA wheels).
# RealtimeSTT depends on torch, and the default PyPI torch drags in all
# the nvidia-* CUDA packages. Pre-installing the CPU build FIRST makes pip
# treat torch/torchaudio as already satisfied, so it skips the CUDA junk.
# (macOS PyTorch ships no CUDA baggage, so it needs nothing special.)
# ------------------------------------------------------------------
step "Setting up PyTorch (GPU or CPU)"
TORCH_CUDA="$("$PY" -c 'import torch; print(torch.version.cuda)' 2>/dev/null || echo missing)"
CUDA_PKGS="$("$PY" -m pip list --format=freeze 2>/dev/null | grep -i "^nvidia-" | cut -d= -f1 || true)"
TORCH_HERE=0
if "$PY" -m pip show torch >/dev/null 2>&1; then TORCH_HERE=1; fi

if [ "$DETECT_OS" = "Darwin" ]; then
    ok "macOS detected - standard PyTorch (no CUDA packages exist for Mac)."

elif has_nvidia_gpu; then
    ok "NVIDIA GPU detected - using CUDA-enabled PyTorch."
    if [ "$TORCH_HERE" = "1" ]; then
        case "$TORCH_CUDA" in
            None|missing)
                # Leftover CPU-only torch (e.g. GPU/drivers added later) —
                # remove it so the requirements install pulls the CUDA build.
                warn "Found CPU-only PyTorch - swapping it for the CUDA build."
                "$PY" -m pip uninstall -y torch torchaudio \
                    || warn "Could not remove old PyTorch - continuing anyway." ;;
        esac
    fi

else
    if command_exists lspci && lspci 2>/dev/null | grep -qi nvidia; then
        warn "NVIDIA card found but no drivers (nvidia-smi shows nothing)."
        warn "Using CPU-only PyTorch - install drivers from https://www.nvidia.com/drivers to use the GPU."
    else
        ok "No NVIDIA GPU - using CPU-only PyTorch (skips ~1.5GB of CUDA downloads)."
    fi
    if [ -n "$CUDA_PKGS" ]; then
        # A previous install pulled CUDA wheels onto this GPU-less machine —
        # remove them to reclaim ~1.5GB.
        warn "Removing leftover CUDA packages from a previous install."
        # shellcheck disable=SC2086
        "$PY" -m pip uninstall -y torch torchaudio $CUDA_PKGS \
            || warn "Could not remove old CUDA packages - continuing anyway."
    fi
    if [ "$TORCH_HERE" = "0" ] || [ -n "$CUDA_PKGS" ]; then
        "$PY" -m pip install --index-url https://download.pytorch.org/whl/cpu torch torchaudio
    else
        ok "CPU-only PyTorch already installed."
    fi
fi

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
    if [ -t 0 ]; then
        read -r KEY || KEY=""
    else
        # Running via `curl ... | bash`: stdin is the download pipe, so read
        # the key from the terminal instead.
        read -r KEY </dev/tty || KEY=""
    fi
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