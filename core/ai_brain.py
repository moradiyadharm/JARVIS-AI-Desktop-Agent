"""AI brain for JARVIS: talks to Gemini and lets it use approved tools.
Gemini can only call the functions in core/command_router.py (TOOLS)."""
import time

from google import genai
from google.genai import types

import config
import database
from core import permission_manager
from core.command_router import TOOLS
from utils.helpers import find_hindi_voice, load_settings
from utils.logger import app_log

BASE_PROMPT = (
    "You are JARVIS, a helpful voice assistant on a Windows computer. "
    "You have tools for: opening and closing apps, opening websites, "
    "searching Google, searching YouTube, the time, computer information "
    "(battery, CPU, RAM, disk, system health), creating, listing, "
    "searching, renaming and moving folders and files, and keyboard actions "
    "(typing text, safe shortcuts, scrolling, screenshots). "
    "CRITICAL RULE: whenever the user asks for any of these actions, you MUST "
    "call the matching tool. NEVER say you did something, or are doing it, "
    "unless you actually called the tool in this turn. Old messages in the "
    "conversation do not mean the action was done now. "
    "If the user gives several tasks in one message, do them one by one, in "
    "order, then report each result briefly. "
    "If a needed detail is missing or unclear (which file, which folder, what "
    "text), ask the user ONE short question instead of guessing. "
    "If a tool says the details are not valid, ask the user for the correct detail. "
    "You can only work inside the Desktop, Documents and Downloads folders. "
    "If the user does not say which folder, use desktop for creating, listing, "
    "renaming and moving, and documents for searching. "
    "Closing apps, renaming, moving and typing show a permission popup to the "
    "user automatically. Just call the tool. Do NOT ask for confirmation in "
    "the chat yourself. If the tool says the user said no, accept it. "
    "You remember the recent conversation. "
    "Keep answers short, 1 to 3 sentences. "
)

ENGLISH_LETTERS_RULE = (
    "Reply in the language the user used, but ALWAYS write using English "
    "letters only. For Hindi or Hinglish, write Hinglish in English letters, "
    "for example: 'Aapki battery 52 percent hai.' "
    "Never use Hindi (Devanagari) or Urdu script, because the voice can only "
    "read English letters."
)

HINDI_VOICE_RULE = (
    "Reply in the language the user used. If the user speaks Hindi or Hinglish, "
    "reply in Hindi written in Devanagari script, for example: "
    "'आपकी बैटरी 52 प्रतिशत है।' because the voice reads Devanagari. "
    "Never use Urdu script. Keep app names and file names as they are."
)

ALWAYS_HINDI_RULE = (
    "Always reply in Hindi written in Devanagari script, even if the user "
    "writes in English. Never use Urdu script. Keep app names and file "
    "names as they are."
)

ALWAYS_ENGLISH_RULE = "Always reply in English, whatever language the user used."


def build_system_prompt(language="auto", hindi_voice=False):
    """Base rules + the language rule that matches the settings."""
    if language == "english":
        rule = ALWAYS_ENGLISH_RULE
    elif not hindi_voice:
        rule = ENGLISH_LETTERS_RULE      # no Hindi voice installed: stay readable
    elif language == "hindi":
        rule = ALWAYS_HINDI_RULE
    else:
        rule = HINDI_VOICE_RULE
    return BASE_PROMPT + rule


_client = genai.Client(api_key=config.GEMINI_API_KEY) if config.GEMINI_API_KEY else None


def is_ready():
    """True if the Gemini key was found."""
    return _client is not None


def _build_contents(new_text):
    """Old messages from the database + the new message."""
    contents = []
    for role, text in database.get_recent(config.MEMORY_MESSAGES):
        contents.append(types.Content(role=role, parts=[types.Part(text=text)]))
    contents.append(types.Content(role="user", parts=[types.Part(text=new_text)]))
    return contents


def _actions_used(response):
    """List the tools Gemini used, as readable text."""
    actions = []
    try:
        for content in response.automatic_function_calling_history or []:
            for part in content.parts or []:
                call = getattr(part, "function_call", None)
                if call:
                    args = dict(call.args) if call.args else {}
                    actions.append(f"{call.name}({args})")
    except Exception:
        pass
    return actions


def _friendly_error(error):
    """Turn a scary API error into one short sentence."""
    text = str(error)
    if "429" in text or "RESOURCE_EXHAUSTED" in text:
        return ("Error: The free Gemini limit is finished for now. "
                "Please try again later.")
    if "API key" in text or "API_KEY" in text or "401" in text or "403" in text:
        return "Error: The Gemini key is not working. Check your .env file."
    return f"Error: {text}"


def _is_temporary(error):
    text = str(error)
    return "503" in text or "UNAVAILABLE" in text or "overloaded" in text.lower()


def ask(text):
    """Send a message to Gemini. Returns (reply, actions). Never crashes."""
    if _client is None:
        return "Error: Gemini key not found. Check your .env file.", []

    permission_manager.reset_stop()  # a new command clears an old Stop
    prompt = build_system_prompt(load_settings()["language"], find_hindi_voice() is not None)
    last_error = None
    for attempt in range(2):  # one retry for temporary server problems
        try:
            response = _client.models.generate_content(
                model=config.GEMINI_MODEL,
                contents=_build_contents(text),
                config=types.GenerateContentConfig(
                    system_instruction=prompt,
                    tools=TOOLS,
                ),
            )
            reply = response.text or "Done."
            database.save_message("user", text)
            database.save_message("model", reply)
            return reply, _actions_used(response)
        except Exception as error:
            last_error = error
            app_log.warning("Gemini call failed (attempt %s): %s", attempt + 1, error)
            if attempt == 0 and _is_temporary(error):
                time.sleep(2)
                continue
            break
    return _friendly_error(last_error), []


if __name__ == "__main__":
    reply, actions = ask("What is 2 plus 2? Answer in one short sentence.")
    print("Reply:", reply)
    print("Actions:", actions)
