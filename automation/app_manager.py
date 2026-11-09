"""App Manager: opens and closes a fixed list of approved apps only."""
import subprocess

import psutil

# name the user says -> (command to open it, process name to close it)
APPROVED_APPS = {
    "notepad": ("notepad", "notepad.exe"),
    "calculator": ("calc", "CalculatorApp.exe"),
    "paint": ("mspaint", "mspaint.exe"),
    "chrome": ("chrome", "chrome.exe"),
    "file explorer": ("explorer", None),  # never closed: it runs the desktop
    "word": ("winword", "WINWORD.EXE"),
    "excel": ("excel", "EXCEL.EXE"),
    "powerpoint": ("powerpnt", "POWERPNT.EXE"),
    "vs code": ("code", "Code.exe"),
}

# Spoken names that mean the same app
ALIASES = {
    "calc": "calculator",
    "google chrome": "chrome",
    "browser": "chrome",
    "explorer": "file explorer",
    "files": "file explorer",
    "visual studio code": "vs code",
    "vscode": "vs code",
    "code": "vs code",
    "ms word": "word",
    "ms excel": "excel",
}


def _normalize(name: str) -> str:
    key = name.lower().strip()
    return ALIASES.get(key, key)


def list_approved_apps() -> str:
    """List the apps JARVIS is allowed to open and close."""
    return "Approved apps: " + ", ".join(APPROVED_APPS) + "."


def open_app(name: str) -> str:
    """Open an approved app on the computer. Approved apps: notepad,
    calculator, paint, chrome, file explorer, word, excel, powerpoint, vs code."""
    key = _normalize(name)
    if key not in APPROVED_APPS:
        return f"I am not allowed to open '{name}'. {list_approved_apps()}"
    command = APPROVED_APPS[key][0]
    subprocess.Popen(f'start "" {command}', shell=True)
    return f"Opened {key}."


def close_app(name: str, confirmed: bool = False) -> str:
    """Close an approved app. This can lose unsaved work, so first ask the
    user to confirm out loud, and only call this with confirmed=True after
    the user clearly said yes."""
    key = _normalize(name)
    if key not in APPROVED_APPS:
        return f"I am not allowed to close '{name}'. {list_approved_apps()}"
    process_name = APPROVED_APPS[key][1]
    if process_name is None:
        return f"I will not close {key}, because it is needed by Windows."
    if not confirmed:
        return (f"Closing {key} may lose unsaved work. "
                f"Ask the user to confirm, then call again with confirmed=True.")

    closed = 0
    for proc in psutil.process_iter(["name"]):
        try:
            if (proc.info["name"] or "").lower() == process_name.lower():
                proc.terminate()
                closed += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    if closed == 0:
        return f"{key} is not running."
    return f"Closed {key}."
