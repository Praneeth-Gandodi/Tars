<#
============================================================================
  TARS - Voice AI Assistant
  Windows installer (PowerShell)
============================================================================
  One command, from any folder:

      Set-ExecutionPolicy -Scope Process Bypass   # once, if needed
      irm https://raw.githubusercontent.com/Praneeth-Gandodi/Tars/dev/install.ps1 | iex

  The script does EVERYTHING for you:
    - Installs Python 3.12 itself (via winget) if it isn't installed yet
    - Clones the project (dev branch) into .\Tars and keeps you on 'dev'
    - Creates a Python 3.12 virtual environment
    - Installs all Python dependencies
    - Installs the Playwright / Chromium browser (browser automation)
    - Sets up .env with your Groq API key
    - Pre-warms the speech-to-text model for instant voice

  You can also run it from inside a Tars folder (it detects and reuses it),
  and it is idempotent: re-run any time to repair or upgrade.

  Flags:
      .\install.ps1 -NoVoice        # skip voice-model prewarming (faster)
      .\install.ps1 -RepoUrl URL    # clone from a different repo URL
      .\install.ps1 -SkipBrowser    # skip Playwright browser install
============================================================================
#>

[CmdletBinding()]
param(
    [string]$RepoUrl = "https://github.com/Praneeth-Gandodi/Tars.git",
    [switch]$NoVoice,
    [switch]$SkipBrowser
)

$ErrorActionPreference = "Stop"

# Bump this whenever installer behavior changes. It prints in the banner so
# pasted logs reveal exactly which script copy ran — raw.githubusercontent.com
# caches for a few minutes, so a re-run right after a fix may use a stale copy.
$InstallerRev = "2026-09-08e"

function Write-Step { param([string]$msg) Write-Host "`n=== $msg ===" -ForegroundColor Cyan }
function Write-Ok    { param([string]$msg) Write-Host "  [OK] $msg" -ForegroundColor Green }
function Write-Warn  { param([string]$msg) Write-Host "  [!!] $msg" -ForegroundColor Yellow }

Write-Host @"
=====================================================================
  TARS  -  Voice AI Assistant  (Windows installer)
  installer rev $InstallerRev (https://github.com/Praneeth-Gandodi/Tars/tree/dev)
=====================================================================
"@ -ForegroundColor Magenta

# ---------------------------------------------------------------
# 1. Locate Python 3.12 — or install it via winget if missing
# ---------------------------------------------------------------
Write-Step "Looking for Python 3.12"

$python = $null
$pythonCmd = $null
foreach ($candidate in @("python", "python3")) {
    try {
        $ver = & $candidate -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
        if ($ver -match "^3\.(12|13)") { $python = $candidate; $pythonCmd = $candidate; break }
    } catch { }
}

if (-not $python) {
    # Fall back to the py launcher (handles multi-version installs).
    try {
        $candidate = "py"
        $ver = & $candidate -3.12 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
        if ($ver -match "^3\.(12|13)") { $python = "py"; $pythonCmd = "$candidate -3.12" }
    } catch { }
}

if (-not $python) {
    Write-Warn "Python 3.12 was not found - installing it now via winget."
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
        # A fresh Python may not be on PATH for this session; locate it directly.
        $candidates = @(
            "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
            "C:\Program Files\Python312\python.exe"
        )
        $found = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
        if ($found) {
            $python = $found
            $pythonCmd = $found
            Write-Ok "Installed Python 3.12 via winget."
        } else {
            Write-Warn "Python was installed but not found on this session's PATH."
            Write-Host  "  Open a NEW terminal and re-run this script."
            exit 1
        }
    } else {
        Write-Host @"

  winget is unavailable. Install Python 3.12 from https://www.python.org/downloads/
  IMPORTANT: on the installer, tick  "Add python.exe to PATH".
  Then open a NEW terminal and re-run this script.

"@
        exit 1
    }
}

Write-Ok "Using Python: $python"

# ---------------------------------------------------------------
# 2. Clone or reuse the project (into .\Tars so the one-liner works)
# ---------------------------------------------------------------
Write-Step "Preparing the project folder"
if (-not (Test-Path ".\tars.py")) {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Write-Warn "git was not found in PATH."
        Write-Host "Install Git from https://git-scm.com/download/win and re-run."
        exit 1
    }
    if (-not (Test-Path ".\Tars")) {
        git clone $RepoUrl Tars
        if ($LASTEXITCODE -ne 0) { Write-Host "Clone failed." -ForegroundColor Red; exit 1 }
        Write-Ok "Cloned TARS."
    } else {
        Write-Ok "Tars folder already exists - reusing it."
    }
    Set-Location ".\Tars"
    # Fresh clones land on the default branch; the install files live on 'dev'.
    git checkout dev 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "On the 'dev' branch."
    } else {
        git fetch origin dev
        git checkout dev
        if ($LASTEXITCODE -ne 0) { Write-Warn "Could not switch to 'dev'. Install files may be missing." }
        Write-Ok "On the 'dev' branch."
    }
} else {
    Write-Ok "tars.py already present in this folder - reusing it."
}

# ---------------------------------------------------------------
# 3. Create the virtual environment
# ---------------------------------------------------------------
Write-Step "Creating a virtual environment"
if (-not (Test-Path ".\.venv")) {
    $venvArgs = @("-m", "venv", ".venv")
    if ($pythonCmd) {
        # $pythonCmd may be "python", "py -3.12", or a full path with spaces.
        if ($pythonCmd -match '^py\s+') {
            # py launcher with an explicit version tag — split command + tag.
            $parts = $pythonCmd -split "\s+", 2
            & $parts[0] $parts[1] @venvArgs
        } else {
            & $pythonCmd @venvArgs
        }
    } else {
        python -m venv .venv
    }
    if ($LASTEXITCODE -ne 0) { Write-Host "Could not create the environment." -ForegroundColor Red; exit 1 }
    Write-Ok "Virtual environment created at .venv"
} else {
    Write-Ok "Virtual environment already exists."
}

$venvPython = ".\.venv\Scripts\python.exe"

# ---------------------------------------------------------------
# 4. Upgrade pip and install Python dependencies
# ---------------------------------------------------------------
Write-Step "Installing Python dependencies (this may take a few minutes)"
& $venvPython -m pip install --upgrade pip

# PyTorch: full CUDA build only when an NVIDIA GPU is usable, tiny CPU-only
# build otherwise (saves ~1.5GB of NVIDIA wheels). RealtimeSTT depends on
# torch, and the default PyPI torch drags in all the nvidia-* CUDA packages.
# Pre-installing the CPU build FIRST makes pip treat torch/torchaudio as
# already satisfied, so it skips the CUDA junk.
Write-Step "Setting up PyTorch (GPU or CPU)"
$torchCuda = ((& $venvPython -c "import torch; print(torch.version.cuda)" 2>$null) | Out-String).Trim()
if (-not $torchCuda) { $torchCuda = "missing" }
$cuPkgs = @((& $venvPython -m pip list --format=freeze 2>$null | Where-Object { $_ -match "^nvidia-" } | ForEach-Object { ($_ -split "==")[0] }))
$torchHere = ((& $venvPython -m pip show torch 2>$null) | Out-String).Trim()

$hasNvidia = $false
try {
    if ((nvidia-smi -L 2>$null) -match "GPU") { $hasNvidia = $true }
} catch { }

if ($hasNvidia) {
    Write-Ok "NVIDIA GPU detected - using CUDA-enabled PyTorch."
    if ($torchHere -and ($torchCuda -eq "None" -or $torchCuda -eq "missing")) {
        # Leftover CPU-only torch (e.g. GPU/drivers added later) — remove it
        # so the requirements install pulls the CUDA build.
        Write-Warn "Found CPU-only PyTorch - swapping it for the CUDA build."
        & $venvPython -m pip uninstall -y torch torchaudio
    }
} else {
    $cardNoDriver = $false
    try {
        if (Get-CimInstance Win32_VideoController -ErrorAction Stop | Where-Object { $_.Name -match "NVIDIA" }) { $cardNoDriver = $true }
    } catch { }
    if ($cardNoDriver) {
        Write-Warn "NVIDIA card found but no drivers (nvidia-smi shows nothing)."
        Write-Host  "        Using CPU-only PyTorch - install drivers from https://www.nvidia.com/drivers to use the GPU."
    } else {
        Write-Ok "No NVIDIA GPU - using CPU-only PyTorch (skips ~1.5GB of CUDA downloads)."
    }
    if ($cuPkgs.Count -gt 0) {
        # A previous install pulled CUDA wheels onto this GPU-less machine —
        # remove them to reclaim ~1.5GB.
        Write-Warn "Removing leftover CUDA packages from a previous install."
        & $venvPython -m pip uninstall -y torch torchaudio @cuPkgs
    }
    if (-not $torchHere -or $cuPkgs.Count -gt 0) {
        & $venvPython -m pip install --index-url https://download.pytorch.org/whl/cpu torch torchaudio
        if ($LASTEXITCODE -ne 0) { Write-Host "CPU torch install failed." -ForegroundColor Red; exit 1 }
    } else {
        Write-Ok "CPU-only PyTorch already installed."
    }
}

& $venvPython -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { Write-Host "Dependency install failed." -ForegroundColor Red; exit 1 }
Write-Ok "Python dependencies installed."

# ---------------------------------------------------------------
# 5. Install ffmpeg (needed for STT pre-processing + video download)
# ---------------------------------------------------------------
Write-Step "Checking ffmpeg"
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    Write-Warn "ffmpeg not found. TARS still runs, but the voice (STT) mode"
    Write-Host  "        and the video downloader need ffmpeg on PATH."
    Write-Host  "        Install it with:  winget install Gyan.FFmpeg   (then open a NEW terminal)"
    Write-Host  "        or grab it from  https://ffmpeg.org/download.html"
} else {
    Write-Ok "ffmpeg found ($((ffmpeg -version 2>$null | Select-Object -First 1)))"
}

# ---------------------------------------------------------------
# 6. Install the Playwright browser (browser automation tools)
# ---------------------------------------------------------------
if (-not $SkipBrowser) {
    Write-Step "Installing Playwright Chromium (browser automation)"
    & $venvPython -m pip install playwright
    & .\.venv\Scripts\playwright.exe install chromium
    if ($LASTEXITCODE -ne 0) {
        Write-Warn "Chromium install had issues. Text + most tools still work;"
        Write-Host  "        run  .\.venv\Scripts\playwright.exe install chromium  later to retry."
    } else {
        Write-Ok "Chromium installed for browser tools."
    }
}

# ---------------------------------------------------------------
# 7. Set up .env with the Groq API key
# ---------------------------------------------------------------
Write-Step "Configuring .env"
if (-not (Test-Path ".\.env")) {
    Copy-Item ".env.example" ".env"
    Write-Ok "Created .env from .env.example"
}

$dotenv = Get-Content ".env" -Raw
if ($dotenv -match "your_groq_api_key_here") {
    $key = Read-Host "  Enter your free Groq API key (https://console.groq.com/keys)"
    if ($key -and $key -ne "your_groq_api_key_here") {
        $dotenv = $dotenv -replace "your_groq_api_key_here", $key
        Set-Content ".env" $dotenv
        Write-Ok "API key saved to .env"
    } else {
        Write-Warn "No key entered - open .env later and paste it into the groq_api= line."
    }
} else {
    Write-Ok ".env already has a key configured."
}

# ---------------------------------------------------------------
# 8. (Optional) Pre-warm the speech-to-text model for instant voice
# ---------------------------------------------------------------
if (-not $NoVoice) {
    Write-Step "Pre-warming the voice recognition model (~250MB, one-time)"
    Write-Host  "  This makes first voice use instant. Skip with: -NoVoice"
    & .\.venv\Scripts\python.exe -c "from faster_whisper import WhisperModel; WhisperModel('small.en', device='cpu', compute_type='int8')"
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "Whisper STT model cached in your user folder."
    } else {
        Write-Warn "Model pre-warm failed - TARS will download it on first voice use instead."
    }
}

# ---------------------------------------------------------------
# 9. Summary
# ---------------------------------------------------------------
Write-Host ""
Write-Host "=====================================================================" -ForegroundColor Green
Write-Host "  TARS installed!" -ForegroundColor Green
Write-Host "=====================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Start TARS:         .\.venv\Scripts\python.exe tars.py"
Write-Host "                     (or:  .venv\Scripts\activate  then  python tars.py)"
Write-Host ""
Write-Host "  Text mode works right away."
Write-Host "  Voice mode needs:" -NoNewline
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    Write-Host ""
    Write-Host "    - ffmpeg on PATH (see the note above)"
} else {
    Write-Host " (ffmpeg present)"
}
Write-Host "    - a working microphone + speakers"
Write-Host ""
Write-Host "  Need help? See INSTALLATION.md"
Write-Host "=====================================================================" -ForegroundColor Green
