"""Command Router: the ONLY door between Gemini and your computer.

Every action Gemini wants to do goes through _execute(), which:
  1. refuses everything if the emergency stop is on
  2. validates the arguments (Pydantic)
  3. asks YOU (popup) before sensitive actions
  4. runs the approved automation function
  5. writes the result to the audit log and the database

Gemini only sees the simple functions at the bottom (TOOLS). It cannot
run any other code, and it cannot approve anything itself."""
from typing import Callable, Literal

from pydantic import BaseModel, Field, ValidationError

import database
from automation import (
    app_manager,
    browser_manager,
    file_manager,
    keyboard_mouse,
    system_manager,
)
from core import permission_manager
from utils.logger import audit


# ---------- argument models (the rules for each tool) ----------
class NoArgs(BaseModel):
    pass


class NameArgs(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class TextArgs(BaseModel):
    text: str = Field(min_length=1, max_length=500)


class QueryArgs(BaseModel):
    query: str = Field(min_length=1, max_length=300)


class SiteArgs(BaseModel):
    name: str = Field(min_length=1, max_length=300)


class CreateFolderArgs(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    location: str = Field(default="desktop", min_length=1, max_length=260)


class LocationArgs(BaseModel):
    location: str = Field(default="desktop", min_length=1, max_length=260)


class SearchFilesArgs(BaseModel):
    query: str = Field(min_length=1, max_length=100)
    location: str = Field(default="documents", min_length=1, max_length=260)
    max_results: int = Field(default=10, ge=1, le=30)


class RenameArgs(BaseModel):
    old_name: str = Field(min_length=1, max_length=100)
    new_name: str = Field(min_length=1, max_length=100)
    location: str = Field(default="desktop", min_length=1, max_length=260)


class MoveArgs(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    destination: str = Field(min_length=1, max_length=260)
    location: str = Field(default="desktop", min_length=1, max_length=260)


class ScrollArgs(BaseModel):
    direction: Literal["up", "down"] = "down"
    amount: int = Field(default=5, ge=1, le=20)


# ---------- the engine ----------
def _problems(error: ValidationError) -> str:
    parts = []
    for item in error.errors():
        field = ".".join(str(p) for p in item["loc"]) or "input"
        parts.append(f"{field}: {item['msg']}")
    return "; ".join(parts)


def _record(tool: str, raw: dict, status: str, result: str) -> None:
    audit(tool, raw, status, result)
    try:
        database.log_execution(tool, raw, status, result)
    except Exception:
        pass  # a database problem must never stop the assistant


def _execute(tool: str, model: type, raw: dict, action: Callable,
             describe: Callable = None) -> str:
    """Validate, ask permission if needed, run, and record. Never raises."""
    if permission_manager.is_stopped():
        message = "Emergency stop is on, so I did not do anything."
        _record(tool, raw, "blocked", message)
        return message

    try:
        args = model(**raw)
    except ValidationError as error:
        problem = _problems(error)
        _record(tool, raw, "invalid", problem)
        return (f"The details are not valid ({problem}). "
                "Ask the user for the missing or correct detail.")

    if permission_manager.needs_approval(tool):
        question = describe(args) if describe else f"Allow JARVIS to run {tool}?"
        if not permission_manager.ask(question):
            message = "The user said no, so I did not do it."
            _record(tool, raw, "denied", message)
            return message
        if permission_manager.is_stopped():
            message = "Emergency stop is on, so I did not do anything."
            _record(tool, raw, "blocked", message)
            return message

    try:
        result = action(args)
    except Exception as error:  # an automation bug must not crash JARVIS
        message = f"That action failed: {error}"
        _record(tool, raw, "error", message)
        return message

    _record(tool, raw, "ok", result)
    return result


# ---------- the tools Gemini can call ----------
# (simple functions with clear names and docstrings: Gemini reads these)

def open_app(name: str) -> str:
    """Open an approved app: notepad, calculator, paint, chrome, file explorer,
    word, excel, powerpoint or vs code."""
    return _execute("open_app", NameArgs, {"name": name},
                    lambda a: app_manager.open_app(a.name))


def close_app(name: str) -> str:
    """Close an approved app. The user is asked for permission automatically."""
    return _execute(
        "close_app", NameArgs, {"name": name},
        lambda a: app_manager.close_app(a.name, confirmed=True),
        lambda a: f"Close {a.name}?\n\nUnsaved work in it may be lost.",
    )


def list_approved_apps() -> str:
    """List the apps JARVIS is allowed to open and close."""
    return _execute("list_approved_apps", NoArgs, {},
                    lambda a: app_manager.list_approved_apps())


def create_folder(name: str, location: str = "desktop") -> str:
    """Create a new folder in desktop, documents or downloads."""
    return _execute("create_folder", CreateFolderArgs,
                    {"name": name, "location": location},
                    lambda a: file_manager.create_folder(a.name, a.location))


def list_folder(location: str = "desktop") -> str:
    """List what is inside desktop, documents or downloads."""
    return _execute("list_folder", LocationArgs, {"location": location},
                    lambda a: file_manager.list_folder(a.location))


def search_files(query: str, location: str = "documents", max_results: int = 10) -> str:
    """Search file and folder names containing the query, inside desktop,
    documents or downloads."""
    return _execute("search_files", SearchFilesArgs,
                    {"query": query, "location": location, "max_results": max_results},
                    lambda a: file_manager.search_files(a.query, a.location, a.max_results))


def rename_item(old_name: str, new_name: str, location: str = "desktop") -> str:
    """Rename a file or folder in desktop, documents or downloads. The user is
    asked for permission automatically."""
    return _execute(
        "rename_item", RenameArgs,
        {"old_name": old_name, "new_name": new_name, "location": location},
        lambda a: file_manager.rename_item(a.old_name, a.new_name, a.location, confirmed=True),
        lambda a: f"Rename '{a.old_name}' to '{a.new_name}' (in {a.location})?",
    )


def move_item(name: str, destination: str, location: str = "desktop") -> str:
    """Move a file or folder from one approved folder to another (destination
    is desktop, documents or downloads). The user is asked for permission
    automatically."""
    return _execute(
        "move_item", MoveArgs,
        {"name": name, "destination": destination, "location": location},
        lambda a: file_manager.move_item(a.name, a.destination, a.location, confirmed=True),
        lambda a: f"Move '{a.name}' from {a.location} to {a.destination}?",
    )


def open_website(name: str) -> str:
    """Open a website: a known name like youtube, gmail or github, or an
    address like example.com."""
    return _execute("open_website", SiteArgs, {"name": name},
                    lambda a: browser_manager.open_website(a.name))


def search_google(query: str) -> str:
    """Search Google and open the results in the browser."""
    return _execute("search_google", QueryArgs, {"query": query},
                    lambda a: browser_manager.search_google(a.query))


def search_youtube(query: str) -> str:
    """Search YouTube for a video or song and open the results."""
    return _execute("search_youtube", QueryArgs, {"query": query},
                    lambda a: browser_manager.search_youtube(a.query))


def type_text(text: str) -> str:
    """Type text into the active window. The user is asked for permission
    automatically."""
    def describe(a):
        preview = a.text if len(a.text) <= 80 else a.text[:80] + "..."
        return (f"Type this text into the active window?\n\n\"{preview}\"\n\n"
                "After you click Yes, click the window where it should go. "
                "Typing starts in 2 seconds.")
    return _execute("type_text", TextArgs, {"text": text},
                    lambda a: keyboard_mouse.type_text(a.text, confirmed=True),
                    describe)


def press_hotkey(name: str) -> str:
    """Press a safe shortcut: copy, paste, cut, select all, undo, redo, save,
    find, new tab or refresh."""
    return _execute("press_hotkey", NameArgs, {"name": name},
                    lambda a: keyboard_mouse.press_hotkey(a.name))


def scroll(direction: str = "down", amount: int = 5) -> str:
    """Scroll the active window up or down. amount is 1 to 20."""
    return _execute("scroll", ScrollArgs, {"direction": direction, "amount": amount},
                    lambda a: keyboard_mouse.scroll(a.direction, a.amount))


def take_screenshot() -> str:
    """Take a screenshot of the whole screen and save it."""
    return _execute("take_screenshot", NoArgs, {},
                    lambda a: keyboard_mouse.take_screenshot())


def get_datetime() -> str:
    """Get the current date and time."""
    return _execute("get_datetime", NoArgs, {}, lambda a: system_manager.get_datetime())


def get_battery() -> str:
    """Get the battery percentage and charging state."""
    return _execute("get_battery", NoArgs, {}, lambda a: system_manager.get_battery())


def get_cpu_usage() -> str:
    """Get the current CPU usage."""
    return _execute("get_cpu_usage", NoArgs, {}, lambda a: system_manager.get_cpu_usage())


def get_ram_usage() -> str:
    """Get the current RAM usage."""
    return _execute("get_ram_usage", NoArgs, {}, lambda a: system_manager.get_ram_usage())


def get_disk_usage() -> str:
    """Get how full the main drive is."""
    return _execute("get_disk_usage", NoArgs, {}, lambda a: system_manager.get_disk_usage())


def get_system_info() -> str:
    """Get basic details about this computer."""
    return _execute("get_system_info", NoArgs, {}, lambda a: system_manager.get_system_info())


def system_diagnostics() -> str:
    """Get a short health report: CPU, RAM, disk and battery together."""
    return _execute("system_diagnostics", NoArgs, {},
                    lambda a: system_manager.system_diagnostics())


# The complete list Gemini is allowed to use
TOOLS = [
    open_app, close_app, list_approved_apps,
    create_folder, list_folder, search_files, rename_item, move_item,
    open_website, search_google, search_youtube,
    type_text, press_hotkey, scroll, take_screenshot,
    get_datetime, get_battery, get_cpu_usage, get_ram_usage,
    get_disk_usage, get_system_info, system_diagnostics,
]
