"""File Manager: safe file and folder actions inside approved folders only."""
import re
import shutil
from pathlib import Path

HOME = Path.home()


def _first_existing(*paths):
    for p in paths:
        if p.exists():
            return p.resolve()
    return None


# JARVIS may only work inside these folders
APPROVED_ROOTS = {
    "desktop": _first_existing(HOME / "OneDrive" / "Desktop", HOME / "Desktop"),
    "documents": _first_existing(HOME / "OneDrive" / "Documents", HOME / "Documents"),
    "downloads": _first_existing(HOME / "Downloads"),
}

MAX_LIST = 30
MAX_SCAN = 20000  # stop searching after this many items (keeps it fast)


def _roots():
    return [p for p in APPROVED_ROOTS.values() if p is not None]


def _is_inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _resolve_location(location: str) -> Path:
    """Turn 'desktop' or a real path into a folder inside the approved roots."""
    key = (location or "").strip().lower()
    if key in APPROVED_ROOTS:
        root = APPROVED_ROOTS[key]
        if root is None:
            raise ValueError(f"I could not find your {key} folder.")
        return root
    path = Path(location).expanduser().resolve()
    if not any(_is_inside(path, root) for root in _roots()):
        raise PermissionError(
            "I am only allowed to work in your Desktop, Documents and Downloads folders."
        )
    if not path.is_dir():
        raise ValueError("That folder does not exist.")
    return path


def _clean_name(name: str) -> str:
    """Reject names that could escape the folder or are not valid on Windows."""
    name = (name or "").strip().rstrip(". ")
    if not name or name in (".", "..") or re.search(r'[\\/:*?"<>|]', name):
        raise ValueError("That name is not allowed. Do not use slashes or special symbols.")
    return name


def create_folder(name: str, location: str = "desktop") -> str:
    """Create a new folder. location can be desktop, documents or downloads."""
    try:
        base = _resolve_location(location)
        folder = base / _clean_name(name)
        if folder.exists():
            return f"A folder named '{folder.name}' already exists in {base.name}."
        folder.mkdir()
        if folder.is_dir():
            return f"Created folder '{folder.name}' in {base.name}."
        return "I tried to create the folder, but could not confirm it."
    except (ValueError, PermissionError, OSError) as e:
        return f"Could not create the folder: {e}"


def list_folder(location: str = "desktop") -> str:
    """List the folders and files inside desktop, documents or downloads."""
    try:
        base = _resolve_location(location)
        items = sorted(base.iterdir(), key=lambda p: p.name.lower())
        folders = [p.name for p in items if p.is_dir()]
        files = [p.name for p in items if p.is_file()]
        if not items:
            return f"{base.name} is empty."

        def short(names):
            shown = names[:MAX_LIST]
            extra = len(names) - len(shown)
            text = ", ".join(shown)
            return text + (f" (and {extra} more)" if extra > 0 else "")

        parts = []
        if folders:
            parts.append(f"Folders: {short(folders)}.")
        if files:
            parts.append(f"Files: {short(files)}.")
        return f"{base.name} has {len(folders)} folders and {len(files)} files. " + " ".join(parts)
    except (ValueError, PermissionError, OSError) as e:
        return f"Could not list the folder: {e}"


def search_files(query: str, location: str = "documents", max_results: int = 10) -> str:
    """Search file and folder names that contain the query text, inside
    desktop, documents or downloads."""
    try:
        base = _resolve_location(location)
        needle = (query or "").strip().lower()
        if not needle:
            return "Tell me what name to search for."
        found, scanned = [], 0
        for path in base.rglob("*"):
            scanned += 1
            if scanned > MAX_SCAN:
                break
            if needle in path.name.lower():
                found.append(f"{path.name} (in {path.parent.name})")
                if len(found) >= max_results:
                    break
        if not found:
            return f"I found nothing named like '{query}' in {base.name}."
        return f"Found {len(found)}: " + "; ".join(found) + "."
    except (ValueError, PermissionError, OSError) as e:
        return f"Could not search: {e}"


def _find_item(name: str, location: str) -> Path:
    """Find exactly one file or folder by name inside an approved folder."""
    base = _resolve_location(location)
    direct = base / _clean_name(name)
    if direct.exists():
        return direct
    matches = []
    scanned = 0
    for path in base.rglob("*"):
        scanned += 1
        if scanned > MAX_SCAN:
            break
        if path.name.lower() == name.strip().lower():
            matches.append(path)
            if len(matches) > 1:
                break
    if not matches:
        raise ValueError(f"I could not find '{name}' in {base.name}.")
    if len(matches) > 1:
        raise ValueError(f"There is more than one '{name}' in {base.name}. Tell me the exact folder.")
    return matches[0]


def rename_item(old_name: str, new_name: str, location: str = "desktop",
                confirmed: bool = False) -> str:
    """Rename a file or folder inside desktop, documents or downloads.
    First ask the user to confirm, and only call with confirmed=True after
    the user clearly said yes."""
    try:
        item = _find_item(old_name, location)
        target = item.with_name(_clean_name(new_name))
        if target.exists():
            return f"'{target.name}' already exists, so I will not rename over it."
        if not confirmed:
            return (f"Rename '{item.name}' to '{target.name}'? "
                    f"Ask the user to confirm, then call again with confirmed=True.")
        item.rename(target)
        if target.exists() and not item.exists():
            return f"Renamed '{item.name}' to '{target.name}'."
        return "I tried to rename it, but could not confirm."
    except (ValueError, PermissionError, OSError) as e:
        return f"Could not rename: {e}"


def move_item(name: str, destination: str, location: str = "desktop",
              confirmed: bool = False) -> str:
    """Move a file or folder into another folder (destination) inside desktop,
    documents or downloads. First ask the user to confirm, and only call with
    confirmed=True after the user clearly said yes."""
    try:
        item = _find_item(name, location)
        dest_dir = _resolve_location(destination)
        target = dest_dir / item.name
        if target.exists():
            return f"'{item.name}' already exists in {dest_dir.name}, so I will not overwrite it."
        if _is_inside(dest_dir, item) and item.is_dir():
            return "I cannot move a folder into itself."
        if not confirmed:
            return (f"Move '{item.name}' to {dest_dir.name}? "
                    f"Ask the user to confirm, then call again with confirmed=True.")
        item.rename(target) if item.drive == target.drive else shutil.move(str(item), str(target))
        if target.exists() and not item.exists():
            return f"Moved '{item.name}' to {dest_dir.name}."
        return "I tried to move it, but could not confirm."
    except (ValueError, PermissionError, OSError) as e:
        return f"Could not move: {e}"
