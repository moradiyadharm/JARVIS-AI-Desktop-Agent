# JARVIS – AI Voice-Based Desktop Automation Agent

**JARVIS** (Just A Rather Very Intelligent System) is a Windows desktop assistant written in Python. You can talk to it or type to it in English and Hindi. It uses Google Gemini to understand requests and then runs only approved actions on your computer: opening apps and websites, managing folders and files, taking screenshots, and reporting system health.

> Student project. Test it on your own Windows PC before you rely on it.

## Features

- Iron Man style HUD: a pulsing orb that shows what JARVIS is doing (standby, listening, processing, speaking, stopped)
- Conversation panel with a typewriter effect for JARVIS's replies
- Action cards on the right: every action JARVIS runs, with its real result (done, denied, blocked, failed)
- Text input and microphone input (Faster-Whisper, stops automatically when you finish speaking)
- Spoken replies in English (Piper `en_US-lessac-medium`) and Hindi (Piper `hi_IN-rohan-medium`, optional)
- Language setting: Auto, English or Hindi
- Gemini function calling. Gemini can only call the 22 approved functions in `core/command_router.py`
- Pydantic validation of every tool argument
- Permission popup before closing apps, renaming, moving, or typing text
- STOP button that blocks all actions until your next command
- Conversation memory and an automation history, both stored in SQLite
- Audit log in `logs/audit.log`
- Permissions window that lists what JARVIS may and may not do

## What JARVIS will never do

Delete files, run terminal commands, click the mouse, run code written by the AI, or touch anything outside the Desktop, Documents and Downloads folders and the approved apps list.

## Requirements

- Windows 10 or 11
- Python 3.12 (3.11 should also work)
- A microphone and speakers or headphones for voice features
- A free Gemini API key from https://aistudio.google.com/apikey

## Setup

1. Open the project folder in VS Code.
2. Create and activate a virtual environment:

```powershell
py -3.12 -m venv venv
.\venv\Scripts\activate
```

3. Install the packages:

```powershell
pip install -r requirements.txt
```

4. Create a file named `.env` in the project folder with one line:

```text
GEMINI_API_KEY=your_key_here
```

Never upload `.env` or share your key.

5. Check the setup:

```powershell
python config.py
```

`Key found` and `English voice` should say `True`.

## Hindi voice (optional)

```powershell
cd voices
python -m piper.download_voices hi_IN-rohan-medium
cd ..
```

This creates `voices\hi_IN-rohan-medium.onnx` (and its `.onnx.json` file). JARVIS detects it automatically. Test it with `python -m core.text_to_speech`.

## Run

```powershell
python main.py
```

## Run the tests

```powershell
python -m pytest tests -q
```

The tests do not use the microphone, the speakers, or Gemini. They should show `61 passed`.

## Build the Windows application

```powershell
pip install pyinstaller
pyinstaller --noconfirm JARVIS.spec
```

The build goes to `dist\JARVIS\`. Before you run `dist\JARVIS\JARVIS.exe`:

- copy the `voices` folder into `dist\JARVIS\`
- copy your `.env` file into `dist\JARVIS\`

The first build keeps a console window so you can read any errors. Once it works, set `console=False` in `JARVIS.spec` and build again.

## Safety

Sensitive actions show a Yes/No popup. The STOP button blocks further actions until your next command. Every attempted action is recorded in the Automation History and in `logs/audit.log`.

## GitHub

Before you push, check that these are not tracked: `.env`, `venv/`, `logs/`, `*.db`, `*.wav`, `voices/`, `settings.json`, `dist/`, `build/`. The included `.gitignore` covers them.

## Disclaimer

This is an educational desktop automation project. Review each action and permission before you use it with important files.
