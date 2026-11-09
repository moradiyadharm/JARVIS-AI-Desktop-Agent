"""Colours and labels for the JARVIS HUD. Change the look here, in one place."""

BG = "#05080d"          # main background (almost black)
PANEL = "#08111b"       # side panels
CYAN = "#00e5ff"        # main neon colour
ORANGE = "#ffb000"
GREEN = "#39ff14"
RED = "#ff3b3b"
GRAY = "#5b6b7a"
TEXT = "#cfe9ff"

STATE_COLORS = {
    "idle": "#1f7a8c",
    "listening": CYAN,
    "thinking": ORANGE,
    "speaking": GREEN,
    "stopped": RED,
}

STATE_WORDS = {
    "idle": "STANDBY",
    "listening": "LISTENING",
    "thinking": "PROCESSING",
    "speaking": "SPEAKING",
    "stopped": "STOPPED",
}


def mix(color, background, strength):
    """Blend a colour into the background. strength 0 = background, 1 = full colour."""
    c = [int(color[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(background[i:i + 2], 16) for i in (1, 3, 5)]
    blended = [round(b[i] + (c[i] - b[i]) * strength) for i in range(3)]
    return "#%02x%02x%02x" % tuple(blended)
