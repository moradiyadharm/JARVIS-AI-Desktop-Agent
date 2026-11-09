"""JARVIS entry point: starts the desktop window."""
from database import init_db
from gui.dashboard import JarvisApp

if __name__ == "__main__":
    init_db()  # create database tables before the window opens
    JarvisApp().mainloop()
