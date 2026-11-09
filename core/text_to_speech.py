"""Text-to-speech for JARVIS: turns text into sound using Piper.
Hindi text (Devanagari) uses the Hindi voice, everything else the English voice."""
import os
import re
import subprocess
import sys
import wave

import numpy as np
import sounddevice as sd

import config
from utils.helpers import find_hindi_voice, is_hindi_text

HINDI_HELP = (
    "The Hindi voice is not installed. In the JARVIS folder run: "
    "cd voices  then  python -m piper.download_voices hi_IN-rohan-medium"
)


def pick_voice(text):
    """Choose the voice file for this text."""
    if is_hindi_text(text):
        hindi = find_hindi_voice()
        if hindi is None:
            raise RuntimeError(HINDI_HELP)
        return hindi
    return config.VOICE_MODEL


def _synthesize_with_api(text, voice_path):
    """Used inside the packaged .exe. There sys.executable is JARVIS.exe,
    so 'python -m piper' cannot run; we call piper's Python API instead."""
    from piper.voice import PiperVoice

    voice = PiperVoice.load(voice_path)
    with wave.open(config.SPEECH_FILE, "wb") as wav_file:
        if hasattr(voice, "synthesize_wav"):
            voice.synthesize_wav(text, wav_file)
        else:
            voice.synthesize(text, wav_file)


def _synthesize_with_subprocess(text, voice_path):
    """Used when running from VS Code (python main.py)."""
    flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    # UTF-8 is needed so Hindi letters reach Piper correctly on Windows
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    subprocess.run(
        [sys.executable, "-m", "piper", "-m", voice_path, "-f", config.SPEECH_FILE],
        input=text.encode("utf-8"),
        check=True,
        creationflags=flags,
        env=env,
    )


def speak(text):
    """Speak the given text out loud (waits until finished)."""
    clean = re.sub(r"[*#_`]", "", text).strip()
    if not clean:
        return
    voice = pick_voice(clean)
    if getattr(sys, "frozen", False):
        _synthesize_with_api(clean, voice)
    else:
        _synthesize_with_subprocess(clean, voice)

    with wave.open(config.SPEECH_FILE, "rb") as wf:
        rate = wf.getframerate()
        data = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
    sd.play(data, rate)
    sd.wait()


def stop():
    """Stop any speech that is playing right now (used by the Stop button)."""
    try:
        sd.stop()
    except Exception:
        pass


if __name__ == "__main__":
    print("English voice test...")
    speak("Hello, I am JARVIS. My English voice works.")
    if find_hindi_voice():
        print("Hindi voice test...")
        speak("नमस्ते, मैं जार्विस हूँ। मैं आपकी मदद के लिए तैयार हूँ।")
    else:
        print(HINDI_HELP)
    print("Done")
