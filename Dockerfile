# TARS — fully self-contained image.
#   docker build -t tars .
#   docker run -it --rm --device /dev/snd --shm-size=1g tars
#
# Local (native) mode works on any host. Voice modes need a working audio
# device, which Docker only passes through on Linux / WSL2 (--device /dev/snd).

FROM python:3.12-slim

WORKDIR /Tars

ENV PYTHONUNBUFFERED=1 \
    IN_DOCKER=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Runtime system libraries:
#   libgomp1        -> ctranslate2 / faster-whisper (STT)
#   libportaudio2   -> sounddevice (microphone + interruptible playback)
#   libpulse0 + libasound2-plugins -> route ALSA/PulseAudio through WSLg
#                                    (audio works in WSL2 via --mount of the
#                                    PulseServer socket; see WSL_DOCKER_GUIDE.md)
#   pulseaudio-utils -> pactl, for in-container audio sanity checks
#   build-essential + portaudio19-dev -> PyAudio (RealtimeSTT dep) compiles
#                                        its C extension from source
#   ffmpeg          -> RealtimeSTT / audio conversions
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        git \
        build-essential \
        portaudio19-dev \
        libgomp1 \
        libportaudio2 \
        libpulse0 \
        libasound2-plugins \
        pulseaudio-utils \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies (markrender comes from git, needs network at build time).
# Install CPU-only PyTorch FIRST — RealtimeSTT requires torch for Silero VAD,
# but the default PyPI torch wheel drags in ~3 GB of CUDA libs TARS never uses.
RUN pip install --no-cache-dir torch torchaudio --index-url https://download.pytorch.org/whl/cpu
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Browser automation runtime (headless Chromium + system deps)
RUN playwright install --with-deps chromium

# Pre-download the whisper STT model so the first run needs no internet.
# compute_type only affects quantisation at load time, so this one step
# warms the cache for both int8 and float32 runs.
RUN python -c "from faster_whisper import WhisperModel; WhisperModel('small.en', device='cpu', compute_type='int8')"

# Application code + bundled Piper TTS voice
COPY . /Tars

ENTRYPOINT ["python", "tars.py"]