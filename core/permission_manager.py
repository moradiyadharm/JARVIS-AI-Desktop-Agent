"""Permission Manager: decides which actions need the user's approval,
and holds the emergency stop switch.

The approval comes from the user clicking Yes in a popup (set by the GUI),
NOT from Gemini. Gemini cannot approve anything on its own."""
import threading
from typing import Callable, Optional

# Actions that can lose work or change the screen: always ask the user first
SENSITIVE_TOOLS = {"close_app", "rename_item", "move_item", "type_text"}

_approver: Optional[Callable[[str], bool]] = None
_stop = threading.Event()


def set_approver(func: Optional[Callable[[str], bool]]) -> None:
    """The GUI gives us a function that shows a Yes/No popup."""
    global _approver
    _approver = func


def needs_approval(tool: str) -> bool:
    return tool in SENSITIVE_TOOLS


def ask(description: str) -> bool:
    """Ask the user. With no approver, or on any error, the answer is NO."""
    if _approver is None:
        return False
    try:
        return bool(_approver(description))
    except Exception:
        return False


def emergency_stop() -> None:
    """After this, every action is refused until reset_stop() is called."""
    _stop.set()


def reset_stop() -> None:
    _stop.clear()


def is_stopped() -> bool:
    return _stop.is_set()


def rules_summary() -> str:
    """A readable list of what JARVIS may and may not do (for the Permissions window)."""
    from automation import app_manager, file_manager, keyboard_mouse

    folders = [f"  {name}: {path if path else 'not found on this computer'}"
               for name, path in file_manager.APPROVED_ROOTS.items()]
    lines = [
        "FOLDERS JARVIS CAN USE",
        *folders,
        "",
        "APPS JARVIS CAN OPEN",
        "  " + ", ".join(app_manager.APPROVED_APPS),
        "",
        "SHORTCUTS JARVIS CAN PRESS",
        "  " + ", ".join(keyboard_mouse.SAFE_HOTKEYS),
        "",
        "ALWAYS ASKS YOU FIRST (popup)",
        "  " + ", ".join(sorted(SENSITIVE_TOOLS)),
        "",
        "NEVER ALLOWED",
        "  Deleting files, running terminal commands, clicking the mouse,",
        "  running code written by the AI, or touching anything outside the",
        "  folders and apps listed above.",
    ]
    return "\n".join(lines)
