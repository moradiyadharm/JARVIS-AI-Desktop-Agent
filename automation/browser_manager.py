"""Browser Manager: opens websites and searches in the default browser (safe)."""
import re
import urllib.parse
import webbrowser

# Websites JARVIS knows by name
SITES = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "gmail": "https://mail.google.com",
    "github": "https://github.com",
    "whatsapp": "https://web.whatsapp.com",
    "chatgpt": "https://chatgpt.com",
    "gemini": "https://gemini.google.com",
    "linkedin": "https://www.linkedin.com",
    "maps": "https://maps.google.com",
}

# A real web address: letters.letters, optional http(s):// and path.
# This rejects javascript:, file:, localhost and raw IP addresses.
_ADDRESS = re.compile(
    r"^(https?://)?([a-z0-9-]+\.)+[a-z]{2,}(:\d+)?(/\S*)?$", re.IGNORECASE
)


def open_website(name: str) -> str:
    """Open a website in the browser. Give a known site name like youtube,
    gmail or github, or a web address like example.com."""
    text = (name or "").strip()
    key = text.lower()
    if key in SITES:
        url = SITES[key]
    elif _ADDRESS.match(text):
        url = text if key.startswith(("http://", "https://")) else "https://" + text
    else:
        return (f"I will not open '{name}'. Give me a known site "
                f"({', '.join(SITES)}) or a normal web address like example.com.")
    webbrowser.open(url)
    return f"Opened {url}."


def search_google(query: str) -> str:
    """Search Google for something and open the results in the browser."""
    query = (query or "").strip()
    if not query:
        return "Tell me what to search for."
    webbrowser.open("https://www.google.com/search?q=" + urllib.parse.quote(query))
    return f"Searched Google for {query}."


def search_youtube(query: str) -> str:
    """Search YouTube for a video or song and open the results page."""
    query = (query or "").strip()
    if not query:
        return "Tell me what to search for."
    webbrowser.open("https://www.youtube.com/results?search_query=" + urllib.parse.quote(query))
    return f"Searched YouTube for {query}."
