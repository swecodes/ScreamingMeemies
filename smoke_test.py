import asyncio
import os
import time
from typing import Literal
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.exceptions import ModelHTTPError, UnexpectedModelBehavior

load_dotenv()
CANDIDATES = ["groq:openai/gpt-oss-120b","groq:qwen/qwen3.8-27b"]

class GhostReply(BaseModel):
    move: Literal["lie","deflect","reveal","whisper"] = Field(description = "The tactic the ghost chooses for this reply.")
    reply: str = Field(description = "The tactic the ghost chooses for this reply.")
    reply: str = Field(description= "What the ghost says out loud, in character.")

INSTRUCTIONS = ("You are Agnes, a dramatic, petty ghost housekeeper who died in 1926.",
                "You secretly hid grandma's dentures and will never admit it.",
                "Stay in character and keep the replies under 40 words.")

# async def is coroutine, basically a fn. that can pause at await keyword mention
async def try_model(model_name:str) -> None:
    agent = Agent(model_name, output_type = GhostReply, instructions = INSTRUCTIONS) 
    start = time.perf_counter()
    try:
        result = await agent.run("Agnes, where were you at 3 AM when the dentures vanished?")
    except ModelHTTPError as e:
        print(f"[{model_name}] HTTP {e.status_code}: {e.body}")
        return
    except UnexpectedModelBehavior as e:
        print(f"[{model_name}] invalid output after retries: {e}")
        return
    elapsed = time.perf_counter() - start
    print(f"[{model_name}] {elapsed:.2f}s")
    print(f"move: {result.output.move}")
    print(f"reply: {result.output.reply}")
    print(f"usage: {result.usage}")

async def main() -> None:
    if not os.getenv("GROQ_API_KEY"):
        raise SystemExit("GROQ_API_KEY is missing. Check your .env file")
    await asyncio.gather(*(try_model(m) for m in CANDIDATES))

if __name__ == "__main__":
    asyncio.run(main())