# to check whether the json format fits the needs
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field, ValidationError
class GhostSheet(BaseModel):
    """One ghost's character sheet: who they are, what they know, what they hide."""
    model_config = ConfigDict(extra="forbid")

    name: str
    room: str = Field(description="Where this ghost haunts.")
    personality: str = Field(description="How the ghost talks and behaves.")
    first_line: str = Field(description="What the ghost says when the player walks in.")
    knows: list[str] = Field(description="True facts this ghost can share.")
    secret: str = Field(description="What the ghost hides from the player.")
    lie: str = Field(description="The ghost's scripted cover story.")
    goal: str = Field(description="What the ghost wants from the player.")
    example_lines: list[str] = Field(description="Sample lines showing how this ghost talks.")

def load_ghosts(folder: str | Path = "ghosts") -> dict[str, GhostSheet]:
    """Load and validate every ghost file in `folder`. Returns {lowercase_name: sheet}."""
    folder = Path(folder)
    if not folder.is_dir():
        raise FileNotFoundError(f"Ghost folder not found: {folder.resolve()}")
    ghosts: dict[str, GhostSheet] = {}
    for path in sorted(folder.glob("*.json")): # to validat json and check against the format of th e file
        try:
            sheet = GhostSheet.model_validate_json(path.read_text(encoding="utf-8"))
        except ValidationError as e:
            raise ValueError(f"{path.name} is not a valid ghost sheet:\n{e}") from e
        key = sheet.name.lower()
        if key in ghosts:
            raise ValueError(f"Duplicate ghost name '{sheet.name}' in {path.name}")
        ghosts[key] = sheet

    if not ghosts:
        raise ValueError(f"No ghost files found in {folder}")
    return ghosts
if __name__ == "__main__":
    for ghost in load_ghosts().values():
        print(f"{ghost.name} haunts the {ghost.room}, knows {len(ghost.knows)} facts")