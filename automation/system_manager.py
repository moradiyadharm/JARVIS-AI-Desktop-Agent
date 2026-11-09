"""System Manager: read-only information about the computer (safe, changes nothing)."""
import os
import platform
from datetime import datetime

import psutil


def get_datetime() -> str:
    """Current date and time."""
    return datetime.now().strftime("It is %I:%M %p on %A, %d %B %Y.")


def get_battery() -> str:
    """Battery percentage and charging state."""
    battery = psutil.sensors_battery()
    if battery is None:
        return "No battery found. This looks like a desktop computer."
    state = "charging" if battery.power_plugged else "not charging"
    return f"Battery is at {battery.percent:.0f} percent and {state}."


def get_cpu_usage() -> str:
    """How busy the processor is right now."""
    percent = psutil.cpu_percent(interval=1)
    return f"CPU usage is {percent:.0f} percent."


def get_ram_usage() -> str:
    """How much memory (RAM) is in use."""
    mem = psutil.virtual_memory()
    used = mem.used / (1024 ** 3)
    total = mem.total / (1024 ** 3)
    return f"RAM usage is {mem.percent:.0f} percent, {used:.1f} GB of {total:.1f} GB."


def get_disk_usage() -> str:
    """How much space is used on the main drive."""
    disk = psutil.disk_usage(os.path.abspath(os.sep))
    free = disk.free / (1024 ** 3)
    total = disk.total / (1024 ** 3)
    return f"Main drive is {disk.percent:.0f} percent full, {free:.0f} GB free of {total:.0f} GB."


def get_system_info() -> str:
    """Basic details about this computer."""
    return (
        f"{platform.system()} {platform.release()}, "
        f"{psutil.cpu_count(logical=True)} processor threads, "
        f"Python {platform.python_version()}."
    )


def system_diagnostics() -> str:
    """A short health report: CPU, RAM, disk and battery together."""
    return " ".join([get_cpu_usage(), get_ram_usage(), get_disk_usage(), get_battery()])
