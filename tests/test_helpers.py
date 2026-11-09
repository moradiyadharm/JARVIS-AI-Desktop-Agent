import json

import config
from utils import helpers


def test_defaults_when_no_settings_file():
    assert helpers.load_settings() == {"language": "auto", "voice_reply": True}


def test_save_and_load_round_trip():
    helpers.save_settings({"language": "hindi", "voice_reply": False})
    assert helpers.load_settings() == {"language": "hindi", "voice_reply": False}


def test_broken_settings_file_gives_defaults():
    with open(config.SETTINGS_FILE, "w") as f:
        f.write("{ this is not json")
    assert helpers.load_settings() == helpers.DEFAULT_SETTINGS


def test_invalid_values_are_ignored():
    with open(config.SETTINGS_FILE, "w") as f:
        json.dump({"language": "klingon", "voice_reply": "yes", "extra": 1}, f)
    assert helpers.load_settings() == helpers.DEFAULT_SETTINGS


def test_only_known_keys_are_saved():
    helpers.save_settings({"language": "english", "voice_reply": True, "api_key": "SECRET"})
    with open(config.SETTINGS_FILE) as f:
        assert "SECRET" not in f.read()


def test_find_hindi_voice(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "VOICES_DIR", str(tmp_path))
    assert helpers.find_hindi_voice() is None
    (tmp_path / "en_US-lessac-medium.onnx").write_text("x")
    assert helpers.find_hindi_voice() is None          # English voice does not count
    (tmp_path / "hi_IN-rohan-medium.onnx").write_text("x")
    assert helpers.find_hindi_voice().endswith("hi_IN-rohan-medium.onnx")


def test_is_hindi_text():
    assert helpers.is_hindi_text("नमस्ते, आप कैसे हैं?")
    assert helpers.is_hindi_text("आपकी battery 52 प्रतिशत है")
    assert not helpers.is_hindi_text("Hello, how are you?")
    assert not helpers.is_hindi_text("Aapki battery 52 percent hai.")
    assert not helpers.is_hindi_text("")
    assert not helpers.is_hindi_text("12345 !!!")
