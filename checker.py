import re  
import sentry_sdk
def leak_word(hiding_place: str) -> str:
    """The word that would give the hiding place away: its LAST word.
    "the hallway vase" -> "vase", "the prize pumpkin" -> "pumpkin"."""
    return hiding_place.split()[-1].lower()

def find_leak(text: str, hiding_place: str) -> str | None:
    word = leak_word(hiding_place)
    if re.search(rf"\b{re.escape(word)}s?\b", text, re.IGNORECASE):
        return word
    return None

def report_leak(ghost: str, word: str, reply: str) -> None:
    sentry_sdk.capture_message(
        f"Leak caught: {ghost} mentioned '{word}'",
        level="warning", 
        tags={"check": "leak", "ghost": ghost, "leaked_word": word},
        extras={"reply": reply},
    )