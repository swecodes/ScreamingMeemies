
from collections import deque  

MAX_HEARD = 5  

class House:
    def __init__(self, ghost_names: list[str]) -> None:
        self._heard: dict[str, deque[str]] = {
            name.lower(): deque(maxlen=MAX_HEARD) for name in ghost_names
        }

    def post_gossip(self, about: str, text: str) -> None:
        
        for name, inbox in self._heard.items():
            if name != about.lower():  
                inbox.append(f"(overheard) {text}")

    def whisper(self, sender: str, to: str, text: str) -> bool:
        
        inbox = self._heard.get(to.lower())
        if inbox is None or to.lower() == sender.lower():
            return False
        inbox.append(f"({sender} whispered to you) {text}")
        return True

    def heard_by(self, name: str) -> list[str]:
        """Everything this ghost has heard recently, oldest first."""
        return list(self._heard.get(name.lower(), []))
if __name__ == "__main__":
    house = House(["Agnes", "Butler", "Gardener", "Grandchild"])
    house.post_gossip("Agnes", "The visitor asked Agnes where she was overnight.")
    house.whisper("Agnes", "Butler", "Cover for me. Say I was in the attic.")
    house.whisper("Agnes", "Ghostzilla", "hi") 

    for ghost in ["Agnes", "Butler", "Gardener"]:
        print(ghost, "→", house.heard_by(ghost))