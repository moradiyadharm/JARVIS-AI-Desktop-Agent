"""Checks that speech uses the right engine in dev mode and in the .exe.
Piper and the speakers are replaced by fakes, so no sound is played."""
import sys
import wave

import numpy as np
import pytest

import config
from core import text_to_speech as tts


@pytest.fixture
def fake_audio(monkeypatch, tmp_path):
    """Write a tiny valid WAV file where Piper would, and record playback."""
    monkeypatch.setattr(config, "SPEECH_FILE", str(tmp_path / "speech.wav"))
    played = []

    def fake_write(text, voice_path):
        with wave.open(config.SPEECH_FILE, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(np.zeros(160, dtype=np.int16).tobytes())

    monkeypatch.setattr(tts.sd, "play", lambda data, rate: played.append(rate))
    monkeypatch.setattr(tts.sd, "wait", lambda: None)
    return fake_write, played


def test_dev_mode_uses_subprocess(monkeypatch, fake_audio):
    write, played = fake_audio
    calls = []
    monkeypatch.delattr(sys, "frozen", raising=False)
    monkeypatch.setattr(tts, "_synthesize_with_subprocess",
                        lambda text, voice: (calls.append("sub"), write(text, voice)))
    monkeypatch.setattr(tts, "_synthesize_with_api",
                        lambda text, voice: calls.append("api"))
    tts.speak("Hello there")
    assert calls == ["sub"]
    assert played == [16000]


def test_exe_mode_uses_piper_api(monkeypatch, fake_audio):
    write, played = fake_audio
    calls = []
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(tts, "_synthesize_with_subprocess",
                        lambda text, voice: calls.append("sub"))
    monkeypatch.setattr(tts, "_synthesize_with_api",
                        lambda text, voice: (calls.append("api"), write(text, voice)))
    tts.speak("Hello there")
    assert calls == ["api"]          # never tries 'python -m piper' inside the .exe
    assert played == [16000]


def test_empty_text_is_not_spoken(monkeypatch, fake_audio):
    calls = []
    monkeypatch.setattr(tts, "_synthesize_with_subprocess", lambda t, v: calls.append(1))
    tts.speak("   *** ")
    assert calls == []


def test_hindi_without_voice_gives_help(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "VOICES_DIR", str(tmp_path))
    with pytest.raises(RuntimeError) as error:
        tts.pick_voice("नमस्ते दुनिया")
    assert "download_voices" in str(error.value)
