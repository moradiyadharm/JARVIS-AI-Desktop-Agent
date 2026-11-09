"""Action cards: one small card per action JARVIS ran, with its real result."""
import customtkinter as ctk

from gui.theme import CYAN, GRAY, GREEN, ORANGE, RED, TEXT

# status from the database -> (label on the card, colour)
STATUS_STYLE = {
    "ok": ("DONE", GREEN),
    "error": ("FAILED", RED),
    "denied": ("DENIED BY YOU", ORANGE),
    "blocked": ("BLOCKED", ORANGE),
    "invalid": ("NEEDS DETAILS", ORANGE),
}
MAX_CARDS = 12


def _short(text, limit=90):
    text = str(text or "").strip()
    return text if len(text) <= limit else text[:limit] + "..."


class ActionCard(ctk.CTkFrame):
    def __init__(self, master, tool, status, detail=""):
        label, color = STATUS_STYLE.get(status, (str(status).upper(), GRAY))
        super().__init__(master, fg_color="#0b1826", border_width=1,
                         border_color=color, corner_radius=8)
        ctk.CTkLabel(self, text=tool.replace("_", " ").upper(), text_color=CYAN,
                     anchor="w", font=ctk.CTkFont(size=12, weight="bold")
                     ).pack(fill="x", padx=12, pady=(10, 0))
        ctk.CTkLabel(self, text=label, text_color=color, anchor="w",
                     font=ctk.CTkFont(size=10, weight="bold")
                     ).pack(fill="x", padx=12)
        ctk.CTkLabel(self, text=_short(detail), text_color=TEXT, anchor="w",
                     justify="left", wraplength=230, font=ctk.CTkFont(size=11)
                     ).pack(fill="x", padx=12, pady=(2, 10))


class ActionPanel(ctk.CTkScrollableFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self._cards = []

    def add(self, tool, status, detail=""):
        card = ActionCard(self, tool, status, detail)
        card.pack(fill="x", padx=4, pady=6)
        self._cards.append(card)
        while len(self._cards) > MAX_CARDS:
            self._cards.pop(0).destroy()
