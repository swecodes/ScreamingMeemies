from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator


class Role(BaseModel):
   
    model_config = ConfigDict(extra="forbid") 
    secret: str = Field(description="What the ghost hides.")
    lie: str = Field(description="The ghost's cover story.")
    goal: str = Field(description="What the ghost wants from the visitor.")


class GuiltyRole(Role):
    hiding_place: str = Field(description="Where this ghost hid the dentures.")
    confession: str = Field(description="Printed when the visitor accuses this ghost correctly.")


class GhostSheet(BaseModel):

    model_config = ConfigDict(extra="forbid")

    name: str
    room: str = Field(description="Where this ghost haunts.")
    personality: str = Field(description="How the ghost talks and behaves.")
    first_line: str = Field(description="What the ghost says when the visitor walks in.")
    example_lines: list[str] = Field(description="Sample lines showing how this ghost talks.")
    knows: list[str] = Field(description="True facts this ghost can share.")
    guilty: GuiltyRole
    innocent: Role
    clue: str = Field(description="Clue template. {culprit} and {place} are filled in each game.")
    farewell: str = Field(description="Said when the case is solved and this ghost was innocent.")
    outrage: str = Field(description="Said when the visitor wrongly accuses this ghost.")

    @field_validator("clue")
    @classmethod
    def clue_placeholders_are_valid(cls, clue: str) -> str:
        try:
            clue.format(culprit="X", place="Y")
        except (KeyError, IndexError, ValueError) as e:
            raise ValueError(f"clue may only use {{culprit}} and {{place}} (problem: {e})") from e
        return clue


def load_ghosts(folder: str | Path = "ghosts") -> dict[str, GhostSheet]:
    folder = Path(folder)
    if not folder.is_dir():
        raise FileNotFoundError(f"Ghost folder not found: {folder.resolve()}")

    ghosts: dict[str, GhostSheet] = {}
    for path in sorted(folder.glob("*.json")):
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