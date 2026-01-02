import wave 
import re
import os
from piper import PiperVoice
from datetime import datetime
from playsound3 import playsound
from rich.console import Console 

console = Console()
Onnx_loaded = False

def clean_text(text):
    text = re.sub(r'[*_]{1,3}', '', text)

    text = re.sub(r'#+\s+', '', text)

    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

    text = text.replace(':', '.')
    text = text.replace(';', ',')

    text = re.sub(r'^[\*\-\+]\s+', ', ', text, flags=re.MULTILINE)

    text = re.sub(r'\n+', '\n', text).strip()
    
    return text

def tts_pipeline(text):
    global Onnx_loaded
    now = datetime.now()
    wav_file_name = now.strftime("%d-%m-%H-%M-%S")
    text = clean_text(text)
    try:
        if not Onnx_loaded:
            voice = PiperVoice.load("./assets/tts_models/en_US-norman-medium.onnx")
            Onnx_loaded = True
    except Exception as e:
        console.print(f"Error: {e}")
    with wave.open(f"{wav_file_name}.wav", "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(22050)    
        for chunk in voice.synthesize(text):
            wav_file.writeframes(chunk.audio_int16_bytes)

    playsound(f"{wav_file_name}.wav", block=True)
    os.remove(f"{wav_file_name}.wav")
    
    
    
