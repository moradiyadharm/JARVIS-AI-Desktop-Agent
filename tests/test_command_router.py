import pytest

import database
from core import command_router as router
from core import permission_manager as pm


@pytest.fixture(autouse=True)
def clean_permissions():
    pm.set_approver(None)
    pm.reset_stop()
    yield
    pm.set_approver(None)
    pm.reset_stop()


def last_execution():
    return database.get_executions(1)[0]


# ---------- argument validation ----------
def test_missing_or_empty_detail_is_invalid():
    result = router.create_folder("")
    assert "not valid" in result
    assert last_execution()[3] == "invalid"


def test_too_long_text_is_invalid():
    assert "not valid" in router.search_google("x" * 400)


def test_scroll_direction_is_checked():
    assert "not valid" in router.scroll("sideways", 3)
    assert "not valid" in router.scroll("down", 500)


def test_valid_call_runs_and_is_recorded():
    result = router.search_google("Python tutorials")
    assert "Python tutorials" in result
    time, tool, args, status, saved = last_execution()
    assert (tool, status) == ("search_google", "ok")


# ---------- permission popup for sensitive actions ----------
def test_sensitive_action_without_approver_is_denied(monkeypatch):
    called = []
    monkeypatch.setattr(router.file_manager, "rename_item",
                        lambda *a, **k: called.append(1) or "renamed")
    assert "said no" in router.rename_item("A", "B")
    assert called == []                       # the real action never ran
    assert last_execution()[3] == "denied"


def test_sensitive_action_user_says_no(monkeypatch):
    called = []
    monkeypatch.setattr(router.app_manager, "close_app",
                        lambda *a, **k: called.append(1) or "closed")
    pm.set_approver(lambda text: False)
    assert "said no" in router.close_app("notepad")
    assert called == []


def test_sensitive_action_user_says_yes(monkeypatch):
    seen = {}

    def fake_close(name, confirmed=False):
        seen["args"] = (name, confirmed)
        return "Closed notepad."

    monkeypatch.setattr(router.app_manager, "close_app", fake_close)
    questions = []
    pm.set_approver(lambda text: questions.append(text) or True)
    assert router.close_app("notepad") == "Closed notepad."
    assert seen["args"] == ("notepad", True)   # confirmed comes from the USER popup
    assert "notepad" in questions[0]
    assert last_execution()[3] == "ok"


def test_every_sensitive_tool_asks(monkeypatch):
    asked = []
    pm.set_approver(lambda text: asked.append(text) or False)
    router.close_app("notepad")
    router.rename_item("A", "B")
    router.move_item("A", "documents")
    router.type_text("hello")
    assert len(asked) == 4


def test_safe_action_never_asks():
    asked = []
    pm.set_approver(lambda text: asked.append(text) or False)
    router.get_battery()
    router.open_website("github")
    assert asked == []


# ---------- emergency stop ----------
def test_emergency_stop_blocks_everything():
    pm.emergency_stop()
    assert "Emergency stop" in router.get_battery()
    assert "Emergency stop" in router.open_app("notepad")
    assert last_execution()[3] == "blocked"


def test_stop_pressed_while_popup_is_open(monkeypatch):
    called = []
    monkeypatch.setattr(router.app_manager, "close_app",
                        lambda *a, **k: called.append(1) or "closed")

    def popup(text):
        pm.emergency_stop()      # user pressed STOP, then clicked Yes
        return True

    pm.set_approver(popup)
    assert "Emergency stop" in router.close_app("notepad")
    assert called == []


# ---------- crashes never escape ----------
def test_automation_crash_is_caught(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("disk exploded")

    monkeypatch.setattr(router.system_manager, "get_battery", boom)
    result = router.get_battery()
    assert "failed" in result and "disk exploded" in result
    assert last_execution()[3] == "error"


def test_tool_list_is_complete_and_unique():
    names = [t.__name__ for t in router.TOOLS]
    assert len(names) == len(set(names)) == 22
    assert all(t.__doc__ for t in router.TOOLS)   # Gemini reads the docstrings
    assert "confirmed" not in " ".join(
        t.__code__.co_varnames[: t.__code__.co_argcount].__repr__() for t in router.TOOLS
    )   # Gemini is never given a 'confirmed' switch
