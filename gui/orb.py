"""The orb: JARVIS's 'face'. Its colour, size and rotating rings show what
JARVIS is doing. It redraws about 25 times a second on the main thread."""
import math
import time
import tkinter as tk

from gui.theme import BG, STATE_COLORS, STATE_WORDS, mix


class Orb(tk.Canvas):
    SIZE = 260
    FRAME_MS = 40

    def __init__(self, master):
        super().__init__(master, width=self.SIZE, height=self.SIZE,
                         bg=BG, highlightthickness=0)
        self.state = "idle"
        self.level = 0.0          # microphone loudness, 0 to 1
        self._tick()

    def set_state(self, state):
        self.state = state if state in STATE_COLORS else "idle"

    def set_level(self, level):
        self.level = max(0.0, min(1.0, level * 12))

    def _tick(self):
        try:
            self.draw(time.time())
        except tk.TclError:
            return  # the window was closed
        self.after(self.FRAME_MS, self._tick)

    def draw(self, now):
        self.delete("all")
        c = self.SIZE / 2
        color = STATE_COLORS[self.state]

        # how big the core is right now
        if self.state == "listening":
            swell = 20 * self.level
        elif self.state == "speaking":
            swell = 10 + 8 * math.sin(now * 9)
        elif self.state == "thinking":
            swell = 6 * math.sin(now * 5)
        else:
            swell = 3 * math.sin(now * 1.5)
        core = 36 + swell

        # soft glow rings, the outer ones are fainter
        for radius, strength in ((core + 36, 0.08), (core + 24, 0.15), (core + 12, 0.28)):
            self.create_oval(c - radius, c - radius, c + radius, c + radius,
                             outline=mix(color, BG, strength), width=2)

        # rotating broken rings (the HUD look)
        for radius, speed, shade in ((core + 44, 70, color), (core + 56, -45, mix(color, BG, 0.5))):
            for k in range(3):
                start = (now * speed + k * 120) % 360
                self.create_arc(c - radius, c - radius, c + radius, c + radius,
                                start=start, extent=70, style="arc",
                                outline=shade, width=2)

        # the core and its label
        self.create_oval(c - core, c - core, c + core, c + core,
                         fill=mix(color, BG, 0.22), outline=color, width=2)
        self.create_text(c, c, text=STATE_WORDS.get(self.state, "STANDBY"),
                         fill=color, font=("Consolas", 11, "bold"))
