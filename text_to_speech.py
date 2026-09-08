import wave
import re
import os
import numpy as np
from piper import PiperVoice
from datetime import datetime
from playsound3 import playsound
from rich.console import Console

console = Console()
Onnx_loaded = False
voice = None

SAMPLE_RATE = 22050
CHUNK = 2048  # frames per write (~93 ms) — keeps interruption responsive


def clean_text(text):
    text = re.sub(r'[*_]{1,3}', '', text)

    text = re.sub(r'`{1,3}', '', text)

    text = re.sub(r'#+\s+', '', text)

    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

    text = text.replace(':', '.')
    text = text.replace(';', ',')

    text = re.sub(r'^[\*\-\+]\s+', ', ', text, flags=re.MULTILINE)

    text = re.sub(r'\n+', '\n', text).strip()
    
    return text


def _play_with_sounddevice(int16_array, interrupt_event=None):
    """Stream the audio in small chunks, stopping instantly if the
    interrupt event is set (the user started speaking)."""
    import sounddevice as sd
    with sd.OutputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16") as stream:
        for i in range(0, len(int16_array), CHUNK):
            if interrupt_event is not None and interrupt_event.is_set():
                break
            stream.write(int16_array[i:i + CHUNK])
    if interrupt_event is not None:
        interrupt_event.clear()


def _synthesize(text, voice):
    """Synthesize text with Piper into a single int16 numpy array."""
    frames = []
    for chunk in voice.synthesize(text):
        frames.append(chunk.audio_int16_bytes)
    return np.frombuffer(b"".join(frames), dtype=np.int16)


def tts_pipeline(text, interrupt_event=None):
    """Speak `text` out loud.

    If `interrupt_event` (a threading.Event) is provided, playback stops
    the moment the event is set — used for voice-to-voice so the user can
    talk over TARS and cut it off.
    """
    global Onnx_loaded, voice

    # Fresh listening window: clear any stale interrupt before we start.
    if interrupt_event is not None:
        interrupt_event.clear()

    text = clean_text(text)
    try:
        if voice is None:
            voice = PiperVoice.load("./assets/tts_models/en_US-norman-medium.onnx")
            Onnx_loaded = True
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    try:
        audio = _synthesize(text, voice)
    except Exception as e:
        console.print(f"[red]Synthesis error: {e}[/red]")
        return

    if interrupt_event is not None:
        try:
            _play_with_sounddevice(audio, interrupt_event)
            return
        except Exception:
            # Fall through to the blocking fallback if sounddevice fails.
            pass

    # Fallback (no sounddevice / no interruption): write a temp wav and play it.
    now = datetime.now()
    wav_file_name = now.strftime("%d-%m-%H-%M-%S") + ".wav"
    try:
        with wave.open(wav_file_name, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(SAMPLE_RATE)
            wav_file.writeframes(audio.tobytes())
        playsound(wav_file_name, block=True)
    except Exception as e:
        console.print(f"[red]Playback error: {e}[/red]")
    finally:
        if os.path.exists(wav_file_name):
            os.remove(wav_file_name)
        if interrupt_event is not None:
            interrupt_event.clear()