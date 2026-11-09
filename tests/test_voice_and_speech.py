"""Voice choice and language handling. No microphone or speaker is used."""
import pytest

import config
from core import speech_to_text as stt
from core import text_to_speech as tts


# ---------- which voice speaks ----------
def test_english_text_uses_english_voice():
    assert tts.pick_voice("Hello, I am JARVIS.") == config.VOICE_MODEL


def test_hindi_text_without_hindi_voice_gives_clear_help(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "VOICES_DIR", str(tmp_path))
    with pytest.raises(RuntimeError) as error:
        tts.pick_voice("नमस्ते")
    assert "download_voices" in str(error.value)


def test_hindi_text_uses_hindi_voice(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "VOICES_DIR", str(tmp_path))
    (tmp_path / "hi_IN-rohan-medium.onnx").write_text("x")
    assert tts.pick_voice("नमस्ते").endswith("hi_IN-rohan-medium.onnx")


# ---------- which language Whisper listens for ----------
class FakeSegment:
    def __init__(self, text):
        self.text = text


class FakeInfo:
    def __init__(self, language):
        self.language = language


class FakeModel:
    """Pretends to be Whisper and remembers how it was called."""

    def __init__(self, first_language):
        self.first_language = first_language
        self.calls = []

    def transcribe(self, audio, language=None):
        self.calls.append(language)
        used = language or self.first_language
        return [FakeSegment(f" text-{used} ")], FakeInfo(used)


def use_fake(monkeypatch, first_language):
    fake = FakeModel(first_language)
    monkeypatch.setattr(stt, "_get_model", lambda: fake)
    return fake


def test_auto_keeps_english(monkeypatch):
    fake = use_fake(monkeypatch, "en")
    assert stt.transcribe(b"audio", "auto") == ("text-en", "en")
    assert fake.calls == [None]


def test_auto_fixes_urdu_to_hindi(monkeypatch):
    fake = use_fake(monkeypatch, "ur")
    assert stt.transcribe(b"audio", "auto") == ("text-hi", "hi")
    assert fake.calls == [None, "hi"]


def test_forced_english_and_hindi(monkeypatch):
    fake = use_fake(monkeypatch, "ur")
    assert stt.transcribe(b"audio", "english")[1] == "en"
    assert stt.transcribe(b"audio", "hindi")[1] == "hi"
    assert fake.calls == ["en", "hi"]
