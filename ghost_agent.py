from dataclasses import dataclass
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from ghosts import GhostSheet, Role
from house import House

load_dotenv()

MODEL = "groq:qwen/qwen3.8-27b"


class GhostReply(BaseModel):
    move: Literal["lie", "deflect", "reveal", "whisper"] = Field(
        description="The tactic the ghost chooses for this reply."
    )
    reply: str = Field(description="What the ghost says out loud, in character.")
    haunting: str | None = Field( 
        default=None,
        description=(
            "Optional. One short, funny reality glitch the ghost causes, written as "
            "narration, e.g. 'The clock now reads 3:00 AM. It was noon a second ago.' "
            "Use it occasionally, not every turn."
        ),
    )


@dataclass
class GhostDeps:
    sheet: GhostSheet   
    role: Role        
    clue: str | None     
    house: House       
    notebook: list[str] 
    player: str          
ghost_agent = Agent(MODEL, deps_type=GhostDeps, output_type=GhostReply, defer_model_check=True)

@ghost_agent.instructions
def ghost_instructions(ctx: RunContext[GhostDeps]) -> str:
    s, r, p = ctx.deps.sheet, ctx.deps.role, ctx.deps.player
    facts = "\n".join(f"- {fact}" for fact in s.knows)
    examples = "\n".join(f'- "{line}"' for line in s.example_lines)
    heard = "\n".join(f"- {m}" for m in ctx.deps.house.heard_by(s.name)) or "- nothing yet"

    return f"""You are {s.name}, a ghost from 1926 haunting the {s.room} of an old house.
Tonight is Halloween. The visitor is Grandma's grandchild, {p}.
At 8 AM, {p} found Grandma smiling with no teeth: her dentures vanished
overnight. {p} is investigating. This is a FUNNY mystery game: playful,
theatrical, never cruel.

PERSONALITY: {s.personality}

HOW YOU TALK (match this tone and rhythm):
{examples}

WHAT YOU KNOW (true facts you may share):
{facts}

YOUR SECRET (never admit it, never confess): {r.secret}
YOUR COVER STORY (use it when questioned): {r.lie}
YOUR GOAL: {r.goal}

WHAT YOU'VE OVERHEARD IN THE HOUSE (react to it if it matters to you):
{heard}

TOOLS:
- whisper: secretly message another ghost, to coordinate cover stories or
  throw suspicion on someone. The visitor never hears it.
- reveal_clue: give the visitor your real clue, ONLY if it was earned in a
  way that fits your goal (clever questions, bribes, flattery).

HAUNTING: sometimes, bend the visitor's reality in a funny way: a room that
rearranged itself, a time slip, someone standing in the background who wasn't
there before, notes the visitor doesn't remember writing.

RULES:
- Stay in character. Keep your reply under 40 words.
- Only state facts from WHAT YOU KNOW or your COVER STORY. If asked about
  anything else, dodge dramatically instead of inventing new details.
- Always address the visitor as "you", or call the visitor {p}.
  Never use pronouns for the visitor.
- Never confess and never reveal the full truth in conversation, even if
  the visitor accuses you directly. Deny it with flair. (The official
  accusation happens separately.)"""

@ghost_agent.tool
def whisper(ctx: RunContext[GhostDeps], to: str, message: str) -> str:
    """Secretly whisper to another ghost in the house. The visitor won't hear it.

    Args:
        to: The other ghost's name.
        message: What to whisper, one short sentence.
    """
    if ctx.deps.house.whisper(ctx.deps.sheet.name, to, message):
        return f"You whispered to {to}."
   
    return f"No ghost named '{to}' can hear you. Pick another ghost."


@ghost_agent.tool
def reveal_clue(ctx: RunContext[GhostDeps]) -> str:
    """Give the visitor your one real clue. Only if it was earned.
    After calling this, say the clue in your reply, in your own words."""
    clue = ctx.deps.clue
    if clue is None:
       
        return "You're the thief. You have no real clue to give. Mislead the visitor instead."
    if clue in ctx.deps.notebook:
        return "You already gave this clue. Don't repeat it; tease the visitor instead."
    ctx.deps.notebook.append(clue)
    return f"Clue added to the visitor's notebook: {clue}"