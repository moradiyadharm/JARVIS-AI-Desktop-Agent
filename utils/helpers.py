"""Small helper functions used by several parts of JARVIS:
saved settings, Hindi voice lookup, and Hindi text detection."""
import glob
import json
import os
from typing import Optional

import config

LANGUAGES = ("auto", "english", "hindi")
DEFAULT_SETTINGS = {"language": "auto", "voice_reply": True}


def load_settings() -> dict:
    """Read settings.json. Missing or broken file gives the defaults."""
    settings = dict(DEFAULT_SETTINGS)
    try:
        with open(config.SETTINGS_FILE, encoding="utf-8") as f:
            saved = json.load(f)
    except (OSError, ValueError):
        return settings
    if isinstance(saved, dict):
        if saved.get("language") in LANGUAGES:
            settings["language"] = saved["language"]
        if isinstance(saved.get("voice_reply"), bool):
            settings["voice_reply"] = saved["voice_reply"]
    return settings


def save_settings(settings: dict) -> None:
    """Save only the settings we know about. A write problem is ignored."""
    clean = {key: settings.get(key, default) for key, default in DEFAULT_SETTINGS.items()}
    try:
        with open(config.SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(clean, f, indent=2)
    except OSError:
        pass


def find_hindi_voice() -> Optional[str]:
    """Path of a downloaded Hindi voice (voices/hi_IN-*.onnx), or None."""
    matches = sorted(glob.glob(os.path.join(config.VOICES_DIR, config.HINDI_VOICE_GLOB)))
    return matches[0] if matches else None


def is_hindi_text(text: str, threshold: float = 0.3) -> bool:
    """True if at least `threshold` of the letters are Devanagari (Hindi script)."""
    letters = [c for c in (text or "") if c.isalpha()]
    if not letters:
        return False
    devanagari = sum(1 for c in letters if "ऀ" <= c <= "ॿ")
    return devanagari / len(letters) >= threshold
