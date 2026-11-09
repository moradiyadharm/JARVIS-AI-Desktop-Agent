from core import permission_manager as pm


def teardown_function():
    pm.set_approver(None)
    pm.reset_stop()


def test_sensitive_tools_need_approval():
    for tool in ("close_app", "rename_item", "move_item", "type_text"):
        assert pm.needs_approval(tool)


def test_safe_tools_do_not_need_approval():
    for tool in ("open_website", "get_battery", "create_folder", "take_screenshot"):
        assert not pm.needs_approval(tool)


def test_no_approver_means_no():
    pm.set_approver(None)
    assert pm.ask("Delete everything?") is False


def test_approver_yes_and_no():
    pm.set_approver(lambda text: True)
    assert pm.ask("ok?") is True
    pm.set_approver(lambda text: False)
    assert pm.ask("ok?") is False


def test_broken_approver_means_no():
    def broken(text):
        raise RuntimeError("popup crashed")

    pm.set_approver(broken)
    assert pm.ask("ok?") is False


def test_emergency_stop_and_reset():
    assert not pm.is_stopped()
    pm.emergency_stop()
    assert pm.is_stopped()
    pm.reset_stop()
    assert not pm.is_stopped()


def test_rules_summary_lists_everything_important():
    text = pm.rules_summary()
    for part in ("FOLDERS JARVIS CAN USE", "desktop", "APPS JARVIS CAN OPEN",
                 "notepad", "SHORTCUTS JARVIS CAN PRESS", "ALWAYS ASKS YOU FIRST",
                 "close_app", "type_text", "NEVER ALLOWED"):
        assert part in text
