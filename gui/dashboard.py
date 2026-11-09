"""JARVIS HUD window (CustomTkinter). It only draws the screen and hands the
real work to the other modules. Long jobs run in background threads, and every
screen update happens on the main thread (through self.after)."""
import os
import threading
from datetime import datetime
from tkinter import messagebox

import customtkinter as ctk

import config
import database
from core import ai_brain, permission_manager, speech_to_text, text_to_speech, voice_input
from gui.action_cards import ActionPanel
from gui.orb import Orb
from gui.theme import BG, CYAN, GRAY, GREEN, PANEL, RED, TEXT
from utils.helpers import find_hindi_voice, load_settings, save_settings

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

PERMISSION_TIMEOUT_SECONDS = 120
TYPING_ENABLED = True        # JARVIS's reply appears one letter group at a time
TYPING_CHARS_PER_STEP = 3
TYPING_STEP_MS = 18
BUTTON_COLOR = "#0f3d4d"
BUTTON_HOVER = "#15566b"


def _state_for(text):
    """Turn a status text into an orb state."""
    lowered = text.lower()
    if "listening" in lowered:
        return "listening"
    if "speaking" in lowered:
        return "speaking"
    if "stopped" in lowered:
        return "stopped"
    if any(word in lowered for word in ("thinking", "understanding", "ready", "waiting")):
        return "thinking"
    return "idle"


class JarvisApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("JARVIS - AI Desktop Agent")
        self.geometry("1200x760")
        self.minsize(1000, 640)
        self.configure(fg_color=BG)

        database.init_db()
        permission_manager.set_approver(self.ask_permission)
        self.settings = load_settings()
        self.busy = False
        self._settings_win = None
        self._permissions_win = None
        self._typing_text = ""
        self._typing_pos = 0
        self._typing_active = False

        self.grid_columnconfigure(0, weight=0, minsize=200)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0, minsize=300)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_center()
        self._build_right_panel()

        self.log("JARVIS", "System online. Gemini connected." if ai_brain.is_ready()
                 else "System online. Gemini key not found.")
        self.log("JARVIS", "Type a command, or click MIC and speak.")

    # =====================================================================
    # Screen parts
    # =====================================================================
    def _hud_button(self, parent, text, command, color=CYAN):
        ctk.CTkButton(parent, text=text, command=command, fg_color="transparent",
                      hover_color="#0a2a33", border_width=1, border_color=color,
                      text_color=color, corner_radius=6, height=34
                      ).pack(fill="x", padx=16, pady=4)

    def _build_sidebar(self):
        side = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color=PANEL)
        side.grid(row=0, column=0, sticky="nsew")
        side.grid_propagate(False)

        ctk.CTkLabel(side, text="J.A.R.V.I.S", text_color=CYAN,
                     font=ctk.CTkFont(size=26, weight="bold")).pack(pady=(26, 0))
        ctk.CTkLabel(side, text="JUST A RATHER VERY INTELLIGENT SYSTEM",
                     text_color=GRAY, wraplength=170,
                     font=ctk.CTkFont(size=9)).pack(pady=(4, 16))

        online = ai_brain.is_ready()
        self.online_label = ctk.CTkLabel(
            side, text="● ONLINE" if online else "● OFFLINE",
            text_color=GREEN if online else RED,
            font=ctk.CTkFont(size=12, weight="bold"))
        self.online_label.pack(pady=(0, 18))

        self._hud_button(side, "Settings", self.open_settings)
        self._hud_button(side, "Permissions", self.open_permissions)
        self._hud_button(side, "History", self.show_history)
        self._hud_button(side, "Automation log", self.show_automation_history)
        self._hud_button(side, "Clear history", self.clear_history, color=RED)

        ctk.CTkButton(side, text="■  STOP", command=self.emergency_stop,
                      fg_color="#2a0b0b", hover_color="#4a1010", border_width=2,
                      border_color=RED, text_color=RED, height=46,
                      font=ctk.CTkFont(size=14, weight="bold")
                      ).pack(fill="x", padx=16, pady=(26, 4))

        self.status = ctk.CTkLabel(side, text="● Idle", text_color="orange")
        self.status.pack(side="bottom", pady=20)
        self.orb_state_hint = None

    def _build_center(self):
        center = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        center.grid(row=0, column=1, sticky="nsew", padx=12, pady=12)
        center.grid_columnconfigure(0, weight=1)
        center.grid_rowconfigure(2, weight=1)

        # top bar: language, voice switch
        top = ctk.CTkFrame(center, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew")
        self.language_menu = ctk.CTkOptionMenu(
            top, values=["Auto", "English", "Hindi"], width=120,
            fg_color="#0a1f2a", button_color=BUTTON_COLOR, button_hover_color=BUTTON_HOVER,
            text_color=CYAN, command=self.on_language_change)
        self.language_menu.set(self.settings["language"].title())
        self.language_menu.pack(side="left")
        self.voice_on = ctk.CTkSwitch(top, text="VOICE REPLY", progress_color=CYAN,
                                      text_color=TEXT, command=self.on_voice_toggle)
        if self.settings["voice_reply"]:
            self.voice_on.select()
        self.voice_on.pack(side="right", padx=6)

        # the orb
        self.orb = Orb(center)
        self.orb.grid(row=1, column=0, pady=(4, 4))

        # conversation
        self.chat = ctk.CTkTextbox(
            center, font=ctk.CTkFont(family="Consolas", size=14), wrap="word",
            fg_color="#060d14", border_color="#0f3d4d", border_width=1,
            text_color=TEXT, corner_radius=10)
        self.chat.grid(row=2, column=0, sticky="nsew", pady=(6, 10))
        self.chat.configure(state="disabled")

        # input row
        bar = ctk.CTkFrame(center, fg_color="transparent")
        bar.grid(row=3, column=0, sticky="ew")
        bar.grid_columnconfigure(0, weight=1)
        self.entry = ctk.CTkEntry(bar, placeholder_text="Type a command...", height=44,
                                  fg_color="#060d14", border_color=CYAN, text_color=TEXT)
        self.entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.entry.bind("<Return>", lambda e: self.send())
        ctk.CTkButton(bar, text="SEND", width=90, height=44, command=self.send,
                      fg_color=BUTTON_COLOR, hover_color=BUTTON_HOVER,
                      border_width=1, border_color=CYAN, text_color=CYAN
                      ).grid(row=0, column=1, padx=(0, 6))
        ctk.CTkButton(bar, text="MIC", width=80, height=44, command=self.start_listening,
                      fg_color=BUTTON_COLOR, hover_color=BUTTON_HOVER,
                      border_width=1, border_color=CYAN, text_color=CYAN
                      ).grid(row=0, column=2)

    def _build_right_panel(self):
        right = ctk.CTkFrame(self, width=300, corner_radius=0, fg_color=PANEL)
        right.grid(row=0, column=2, sticky="nsew")
        right.grid_propagate(False)
        ctk.CTkLabel(right, text="ACTIONS", text_color=CYAN,
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(24, 2))
        ctk.CTkLabel(right, text="Every action JARVIS runs appears here.",
                     text_color=GRAY, wraplength=240,
                     font=ctk.CTkFont(size=10)).pack(pady=(0, 8))
        self.actions = ActionPanel(right)
        self.actions.pack(fill="both", expand=True, padx=8, pady=(0, 16))

    # =====================================================================
    # Helpers
    # =====================================================================
    def _write(self, text):
        self.chat.configure(state="normal")
        self.chat.insert("end", text)
        self.chat.configure(state="disabled")
        self.chat.see("end")

    def log(self, who, message):
        stamp = datetime.now().strftime("%H:%M:%S")
        self._write(f"[{stamp}] {who}: {message}\n")

    def set_status(self, text, color):
        self.status.configure(text=text, text_color=color)
        self.orb.set_state(_state_for(text))

    def finish(self):
        self.busy = False
        self.orb.set_level(0)
        self.set_status("● Idle", "orange")

    # =====================================================================
    # Typewriter effect for JARVIS's replies
    # =====================================================================
    def _type_reply(self, reply):
        stamp = datetime.now().strftime("%H:%M:%S")
        self._write(f"[{stamp}] JARVIS: ")
        if not TYPING_ENABLED:
            self._write(reply + "\n")
            return
        if self._typing_active:  # finish the previous reply first
            self._write(self._typing_text[self._typing_pos:] + "\n")
        self._typing_text = reply
        self._typing_pos = 0
        self._typing_active = True
        self._type_step()

    def _type_step(self):
        if not self._typing_active:
            return
        chunk = self._typing_text[self._typing_pos:self._typing_pos + TYPING_CHARS_PER_STEP]
        if chunk:
            self._write(chunk)
            self._typing_pos += TYPING_CHARS_PER_STEP
            self.after(TYPING_STEP_MS, self._type_step)
        else:
            self._typing_active = False
            self._write("\n")

    # =====================================================================
    # Permission popup (called from a background thread)
    # =====================================================================
    def ask_permission(self, description):
        answer = {"ok": False}
        done = threading.Event()

        def show():
            try:
                self.set_status("● Waiting for you...", "yellow")
                answer["ok"] = messagebox.askyesno(
                    "JARVIS needs your permission", description, parent=self)
            finally:
                done.set()

        self.after(0, show)
        done.wait(PERMISSION_TIMEOUT_SECONDS)
        self.after(0, self.log, "Permission", "Allowed" if answer["ok"] else "Denied")
        self.after(0, self.set_status, "● Thinking...", "cyan")
        return answer["ok"]

    # =====================================================================
    # Emergency stop
    # =====================================================================
    def emergency_stop(self):
        permission_manager.emergency_stop()
        text_to_speech.stop()
        if self._typing_active:
            self._typing_active = False
            self._write(self._typing_text[self._typing_pos:] + "\n")
        self.log("System", "STOP pressed. All actions are blocked until your next command.")
        self.set_status("● Stopped", "red")

    # =====================================================================
    # Settings the user can change
    # =====================================================================
    def on_language_change(self, choice):
        self.settings["language"] = choice.lower()
        save_settings(self.settings)
        self.log("System", f"Language set to {choice}.")
        if choice == "Hindi" and find_hindi_voice() is None:
            self.log("System", "Hindi voice is not installed yet, so replies stay readable in English letters.")

    def on_voice_toggle(self):
        self.settings["voice_reply"] = bool(self.voice_on.get())
        save_settings(self.settings)

    def open_settings(self):
        if self._settings_win is not None and self._settings_win.winfo_exists():
            self._settings_win.focus()
            return
        win = ctk.CTkToplevel(self, fg_color=BG)
        win.title("JARVIS Settings")
        win.geometry("540x360")
        self._settings_win = win

        hindi = find_hindi_voice()
        rows = [
            ("Gemini model", config.GEMINI_MODEL),
            ("Listening model (Whisper)", config.WHISPER_MODEL),
            ("English voice", "found" if os.path.exists(config.VOICE_MODEL) else "missing"),
            ("Hindi voice", os.path.basename(hindi) if hindi else "not installed"),
            ("Language", self.settings["language"].title()),
            ("Voice reply", "on" if self.settings["voice_reply"] else "off"),
            ("Logs folder", config.LOGS_DIR),
        ]
        for label, value in rows:
            row = ctk.CTkFrame(win, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=3)
            ctk.CTkLabel(row, text=label, width=200, anchor="w", text_color=GRAY).pack(side="left")
            ctk.CTkLabel(row, text=value, anchor="w", wraplength=280, justify="left",
                         text_color=TEXT).pack(side="left")

        ctk.CTkLabel(win, text="Change Language and Voice reply on the main screen.",
                     text_color=GRAY).pack(pady=(14, 6))
        ctk.CTkButton(win, text="Open logs folder", command=self.open_logs_folder,
                      fg_color=BUTTON_COLOR, hover_color=BUTTON_HOVER).pack(pady=6)

    def open_logs_folder(self):
        os.makedirs(config.LOGS_DIR, exist_ok=True)
        if hasattr(os, "startfile"):
            os.startfile(config.LOGS_DIR)
        else:
            self.log("System", f"Logs are in: {config.LOGS_DIR}")

    def open_permissions(self):
        if self._permissions_win is not None and self._permissions_win.winfo_exists():
            self._permissions_win.focus()
            return
        win = ctk.CTkToplevel(self, fg_color=BG)
        win.title("JARVIS Permissions")
        win.geometry("640x480")
        self._permissions_win = win
        box = ctk.CTkTextbox(win, font=ctk.CTkFont(family="Consolas", size=13), wrap="word",
                             fg_color="#060d14", text_color=TEXT)
        box.pack(fill="both", expand=True, padx=15, pady=15)
        box.insert("end", permission_manager.rules_summary())
        box.configure(state="disabled")

    # =====================================================================
    # History views (written into the conversation)
    # =====================================================================
    def show_history(self):
        rows = database.get_history(20)
        if not rows:
            self.log("System", "History is empty.")
            return
        self.log("System", "----- Last 20 saved messages -----")
        for created_at, role, text in rows:
            who = "You" if role == "user" else "JARVIS"
            short = text if len(text) <= 120 else text[:120] + "..."
            self.log("History", f"({created_at}) {who}: {short}")
        self.log("System", "----- End of history -----")

    def show_automation_history(self):
        rows = database.get_executions(15)
        if not rows:
            self.log("System", "No actions have been run yet.")
            return
        self.log("System", "----- Last 15 actions -----")
        for created_at, tool, args, status, result in rows:
            short = result if len(result) <= 90 else result[:90] + "..."
            self.log("Automation", f"({created_at}) {tool} [{status}] {short}")
        self.log("System", "----- End of actions -----")

    def clear_history(self):
        database.clear_history()
        self.log("System", "History cleared. I forgot our old chat.")

    # =====================================================================
    # Typing
    # =====================================================================
    def send(self):
        text = self.entry.get().strip()
        if not text or self.busy:
            return
        self.entry.delete(0, "end")
        self.log("You", text)
        self.busy = True
        self.set_status("● Thinking...", "cyan")
        threading.Thread(target=self.ask_brain, args=(text,), daemon=True).start()

    # =====================================================================
    # Voice input
    # =====================================================================
    def start_listening(self):
        if self.busy:
            return
        self.busy = True
        threading.Thread(target=self.listen_and_answer, daemon=True).start()

    def _on_level(self, level):
        """Called from the recording thread with the current loudness."""
        self.orb.set_level(level)

    def listen_and_answer(self):
        try:
            self.after(0, self.set_status, "● Getting ready...", "cyan")
            audio = voice_input.record_until_silence(
                on_ready=lambda: self.after(0, self.set_status, "● Listening...", "red"),
                on_level=self._on_level,
            )
            if audio is None:
                self.after(0, self.log, "JARVIS", "I did not hear anything. Try again.")
                self.after(0, self.finish)
                return

            self.after(0, self.set_status, "● Understanding...", "cyan")
            text, _language = speech_to_text.transcribe(audio, self.settings["language"])
            if not text:
                self.after(0, self.log, "JARVIS", "I could not understand. Try again.")
                self.after(0, self.finish)
                return

            self.after(0, self.log, "You (voice)", text)
            self.after(0, self.set_status, "● Thinking...", "cyan")
            self.ask_brain(text)
        except Exception as e:
            self.after(0, self.log, "System", f"Mic error: {e}")
            self.after(0, self.finish)

    # =====================================================================
    # Brain, action cards and voice output
    # =====================================================================
    def ask_brain(self, text):
        reply, actions = ai_brain.ask(text)
        rows = database.get_executions(len(actions)) if actions else []
        self.after(0, self.show_actions, actions, rows)
        self.after(0, self.show_reply, reply)

    def show_actions(self, actions, rows):
        """One card per action. The real status comes from the database."""
        if rows and len(rows) >= len(actions):
            for _time, tool, _args, status, result in rows[-len(actions):]:
                self.actions.add(tool, status, result)
        else:
            for action in actions:
                self.actions.add(action.split("(")[0], "ok", "")

    def show_reply(self, reply):
        self._type_reply(reply)
        if self.settings["voice_reply"] and not reply.startswith("Error:"):
            self.set_status("● Speaking...", "green")
            threading.Thread(target=self.speak_reply, args=(reply,), daemon=True).start()
        else:
            self.finish()

    def speak_reply(self, reply):
        try:
            text_to_speech.speak(reply)
        except Exception as e:
            self.after(0, self.log, "System", f"Voice error: {e}")
        self.after(0, self.finish)
