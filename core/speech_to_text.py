"""Speech-to-text for JARVIS: turns recorded audio into text (Faster-Whisper)."""
from faster_whisper import WhisperModel

import config

_model = None


def _get_model():
    """Load the model only the first time it is needed."""
    global _model
    if _model is None:
        _model = WhisperModel(config.WHISPER_MODEL, device="cpu", compute_type="int8")
    return _model


def transcribe(audio, language_setting="auto"):
    """Convert audio (numpy array) to text. Returns (text, language_code).
    language_setting: "auto", "english" or "hindi"."""
    model = _get_model()
    forced = {"english": "en", "hindi": "hi"}.get(language_setting)
    segments, info = model.transcribe(audio, language=forced)
    language = info.language
    # Whisper often mistakes spoken Hindi for Urdu, so ask again as Hindi
    if forced is None and language == "ur":
        segments, info = model.transcribe(audio, language="hi")
        language = "hi"
    text = " ".join(s.text for s in segments).strip()
    return text, language


if __name__ == "__main__":
    from core.voice_input import record_until_silence

    print("Loading... then speak when you see SPEAK NOW.")
    audio = record_until_silence(on_ready=lambda: print(">>> SPEAK NOW"))
    if audio is None:
        print("I did not hear anything.")
    else:
        text, language = transcribe(audio)
        print("Language:", language)
        print("You said:", text)
