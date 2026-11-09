"""Keyboard/Mouse Manager: typing, scrolling, safe hotkeys and screenshots.
Clicking and mouse moving are NOT included on purpose (planned for Stage 7)."""
import time
from datetime import datetime
from pathlib import Path

import pyautogui
import pyperclip

import config

pyautogui.FAILSAFE = True   # move the mouse to a screen corner to stop everything
pyautogui.PAUSE = 0.2

SCREENSHOT_DIR = Path(config.BASE_DIR) / "screenshots"
MAX_TYPE_LENGTH = 500

# Only these shortcuts are allowed (never Alt+F4, Win+R, etc.)
SAFE_HOTKEYS = {
    "copy": ("ctrl", "c"),
    "paste": ("ctrl", "v"),
    "cut": ("ctrl", "x"),
    "select all": ("ctrl", "a"),
    "undo": ("ctrl", "z"),
    "redo": ("ctrl", "y"),
    "save": ("ctrl", "s"),
    "find": ("ctrl", "f"),
    "new tab": ("ctrl", "t"),
    "refresh": ("f5",),
}


def type_text(text: str, confirmed: bool = False) -> str:
    """Type text into whichever window is active right now. The text goes
    wherever the cursor is, so first ask the user to confirm, and only call
    with confirmed=True after the user clearly said yes."""
    text = text or ""
    if not text.strip():
        return "Tell me what to type."
    if len(text) > MAX_TYPE_LENGTH:
        return f"That text is too long. I only type up to {MAX_TYPE_LENGTH} characters."
    if not confirmed:
        return ("I will type this into the active window: "
                f"'{text[:80]}'. Ask the user to confirm, then call again with "
                "confirmed=True.")
    time.sleep(2)  # gives the user 2 seconds to click the right window
    # pasting works for Hindi and any symbol; typing key by key does not
    old_clipboard = pyperclip.paste()
    try:
        pyperclip.copy(text)
        pyautogui.hotkey("ctrl", "v")
    finally:
        pyperclip.copy(old_clipboard)
    return "Typed the text."


def press_hotkey(name: str) -> str:
    """Press a safe keyboard shortcut. Allowed: copy, paste, cut, select all,
    undo, redo, save, find, new tab, refresh."""
    key = (name or "").strip().lower()
    if key not in SAFE_HOTKEYS:
        return f"I am not allowed to press '{name}'. Allowed: {', '.join(SAFE_HOTKEYS)}."
    pyautogui.hotkey(*SAFE_HOTKEYS[key])
    return f"Pressed {key}."


def scroll(direction: str = "down", amount: int = 5) -> str:
    """Scroll the active window up or down. amount is 1 to 20."""
    direction = (direction or "").strip().lower()
    if direction not in ("up", "down"):
        return "Direction must be up or down."
    amount = max(1, min(int(amount), 20))
    pyautogui.scroll(amount * 100 if direction == "up" else -amount * 100)
    return f"Scrolled {direction}."


def take_screenshot() -> str:
    """Take a screenshot of the whole screen and save it in the screenshots folder."""
    SCREENSHOT_DIR.mkdir(exist_ok=True)
    path = SCREENSHOT_DIR / f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    pyautogui.screenshot(str(path))
    if path.exists():
        return f"Screenshot saved as {path.name} in the screenshots folder."
    return "I tried to take a screenshot, but could not confirm it."
