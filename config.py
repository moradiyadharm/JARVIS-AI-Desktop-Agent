"""Central settings for JARVIS. Every other file imports from here."""
import glob
import os
import sys

from dotenv import load_dotenv

# ---------- Folders ----------
# In the packaged JARVIS.exe, .env, voices and logs live next to the .exe.
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

LOGS_DIR = os.path.join(BASE_DIR, "logs")
VOICES_DIR = os.path.join(BASE_DIR, "voices")
DB_PATH = os.path.join(BASE_DIR, "jarvis.db")
SPEECH_FILE = os.path.join(BASE_DIR, "speech.wav")
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")  # your saved choices

# ---------- Secrets (read from the .env file) ----------
load_dotenv(os.path.join(BASE_DIR, ".env"))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ---------- AI ----------
GEMINI_MODEL = "gemini-3.5-flash-lite"
MEMORY_MESSAGES = 10  # how many old messages JARVIS remembers

# ---------- Voice ----------
VOICE_MODEL = os.path.join(VOICES_DIR, "en_US-lessac-medium.onnx")  # English voice
HINDI_VOICE_GLOB = "hi_IN-*.onnx"   # any Hindi voice downloaded into voices/
WHISPER_MODEL = "base"              # "small" understands Hindi better but is slower
SAMPLE_RATE = 16000

# ---------- App ----------
APP_NAME = "JARVIS"
APP_FULL_NAME = "Just A Rather Very Intelligent System"


if __name__ == "__main__":
    print("Base folder   :", BASE_DIR)
    print("Key found     :", bool(GEMINI_API_KEY))
    print("English voice :", os.path.exists(VOICE_MODEL))
    print("Hindi voice   :", bool(glob.glob(os.path.join(VOICES_DIR, HINDI_VOICE_GLOB))))
