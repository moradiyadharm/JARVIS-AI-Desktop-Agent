"""Tests for the AI brain that need NO internet and use no Gemini requests."""
import database
from core import ai_brain


def test_no_key_gives_a_clear_error(monkeypatch):
    monkeypatch.setattr(ai_brain, "_client", None)
    reply, actions = ai_brain.ask("hello")
    assert reply.startswith("Error:") and ".env" in reply
    assert actions == []


def test_friendly_quota_error():
    message = ai_brain._friendly_error(Exception("429 RESOURCE_EXHAUSTED quota"))
    assert "limit" in message and message.startswith("Error:")


def test_temporary_errors_are_detected():
    assert ai_brain._is_temporary(Exception("503 UNAVAILABLE"))
    assert not ai_brain._is_temporary(Exception("429 RESOURCE_EXHAUSTED"))


def test_memory_is_loaded_in_order():
    database.save_message("user", "my name is Rahul")
    database.save_message("model", "Nice to meet you")
    contents = ai_brain._build_contents("what is my name")
    assert len(contents) == 3
    assert contents[-1].role == "user"


# ---------- the language rules in the prompt ----------
def test_prompt_always_forces_tool_use():
    for language in ("auto", "english", "hindi"):
        for hindi_voice in (True, False):
            assert "MUST" in ai_brain.build_system_prompt(language, hindi_voice)


def test_without_hindi_voice_replies_use_english_letters():
    prompt = ai_brain.build_system_prompt("auto", hindi_voice=False)
    assert "English letters" in prompt
    prompt = ai_brain.build_system_prompt("hindi", hindi_voice=False)
    assert "English letters" in prompt          # no voice, so stay readable


def test_with_hindi_voice_replies_use_devanagari():
    assert "Devanagari" in ai_brain.build_system_prompt("auto", hindi_voice=True)
    assert "Always reply in Hindi" in ai_brain.build_system_prompt("hindi", hindi_voice=True)


def test_english_setting_wins():
    prompt = ai_brain.build_system_prompt("english", hindi_voice=True)
    assert "Always reply in English" in prompt


def test_failed_call_does_not_crash(monkeypatch):
    class BrokenClient:
        class models:
            @staticmethod
            def generate_content(**kwargs):
                raise RuntimeError("network is down")

    monkeypatch.setattr(ai_brain, "_client", BrokenClient)
    reply, actions = ai_brain.ask("hello")
    assert reply.startswith("Error:")
    assert database.get_recent(5) == []     # nothing is saved for a failed call
