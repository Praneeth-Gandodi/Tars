<#
============================================================================
  TARS - Voice AI Assistant
  Windows installer (PowerShell)
============================================================================
  - Creates a Python 3.12 virtual environment
  - Installs Python dependencies
  - Installs the Playwright / Chromium browser (browser automation tools)
  - Sets up .env with your Groq API key
  - (Optional) pre-warms the speech-to-text model so voice mode is instant

  Run it from PowerShell:
      Set-ExecutionPolicy -Scope Process Bypass   # once, if needed
      .\install.ps1

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

function Write-Step { param([string]$msg) Write-Host "`n=== $msg ===" -ForegroundColor Cyan }
function Write-Ok    { param([string]$msg) Write-Host "  [OK] $msg" -ForegroundColor Green }
function Write-Warn  { param([string]$msg) Write-Host "  [!!] $msg" -ForegroundColor Yellow }

Write-Host @"
=====================================================================
  TARS  -  Voice AI Assistant  (Windows installer)
=====================================================================
"@ -ForegroundColor Magenta

# ---------------------------------------------------------------
# 1. Locate Python 3.12
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
    Write-Warn "Python 3.12 was not found."
    Write-Host @"

  Install Python 3.12 from https://www.python.org/downloads/
  IMPORTANT: on the installer, tick  "Add python.exe to PATH".

  Then re-run this script.

"@
    exit 1
}

Write-Ok "Using Python: $python"

# ---------------------------------------------------------------
# 2. Clone or reuse the project
# ---------------------------------------------------------------
Write-Step "Preparing the project folder"
if (-not (Test-Path ".\tars.py")) {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Write-Warn "git was not found in PATH."
        Write-Host "Install Git from https://git-scm.com/download/win and re-run."
        exit 1
    }
    git clone $RepoUrl .
    if ($LASTEXITCODE -ne 0) { Write-Host "Clone failed." -ForegroundColor Red; exit 1 }
    Write-Ok "Cloned TARS from $RepoUrl"
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
        # $pythonCmd may be "python" or "py -3.12" — expand by context.
        if ($pythonCmd -match " ") {
            $parts = $pythonCmd -split " ", 2
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

$pip = ".\.venv\Scripts\python.exe -m pip"

# ---------------------------------------------------------------
# 4. Upgrade pip and install Python dependencies
# ---------------------------------------------------------------
Write-Step "Installing Python dependencies (this may take a few minutes)"
& $pip install --upgrade pip
& $pip install -r requirements.txt
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
    & $pip install playwright
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
