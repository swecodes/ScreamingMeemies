import asyncio
import os
import random
import uuid
from observability import init_sentry
from pydantic_ai.exceptions import ModelHTTPError, UnexpectedModelBehavior

from ghost_agent import GhostDeps, ghost_agent  
from ghosts import GhostSheet, load_ghosts
from house import House
from memory_store import MemoryStore

DEBUG = os.getenv("DEBUG") == "1"
ITALIC, RESET = "\033[3m", "\033[0m" 
MAX_WRONG = 3  

HELP = """Commands:
  /look            who haunts which room
  /go <room>       walk into a room
  /notes           clues you've collected + guesses left
  /accuse <ghost>  name the thief (3 wrong guesses and the ghosts win)
  /quit            leave (your mystery is saved)
Anything else you type is said to the ghost in your room."""


def pick_culprit(ghosts: dict[str, GhostSheet], last: str | None) -> str:
    """Random culprit, never the same as last game's.
    `or list(ghosts)`: with only one ghost, allow the repeat instead of crashing."""
    choices = [name for name in ghosts if name != last] or list(ghosts)
    return random.choice(choices)


async def main() -> None:
    init_sentry()
    if not os.getenv("GROQ_API_KEY"):
        raise SystemExit("GROQ_API_KEY is missing. Check your .env file.")

    ghosts = load_ghosts()
    rooms = {g.room.lower(): g for g in ghosts.values()}  
    store = MemoryStore()
    await store.connect()
    player = input("What's your name, visitor? ").strip() or "visitor"
    record = await store.get_player(player)
    active = record.get("active")
    if active and active.get("culprit") in ghosts:
        game_id, culprit = active["game_id"], active["culprit"]
        wrong = active.get("wrong", 0) 
        print(f"\n(Resuming your unfinished mystery. Wrong guesses so far: {wrong}/{MAX_WRONG})")
    else:
        game_id = uuid.uuid4().hex[:8]  
        culprit = pick_culprit(ghosts, record.get("last_culprit"))
        wrong = 0
        await store.start_game(player, game_id, culprit)

    thief = ghosts[culprit]
    place = thief.guilty.hiding_place
    house = House([g.name for g in ghosts.values()])
    notebook: list[str] = []
    histories: dict[str, list] = {}  
    def deps_for(ghost: GhostSheet) -> GhostDeps:
        """Build this ghost's runtime deps for THIS game."""
        is_thief = ghost.name.lower() == culprit
        return GhostDeps(
            sheet=ghost,
            role=ghost.guilty if is_thief else ghost.innocent,
            # The thief gets no clue; everyone else's clue points at the thief.
            clue=None if is_thief else ghost.clue.format(culprit=thief.name, place=place),
            house=house,
            notebook=notebook,
            player=player,
        )

    print("\nIt's 8 AM on Halloween. Grandma smiles at you... with no teeth.")
    print("Her dentures vanished overnight. The house's ghosts know something.\n")
    print(HELP)

    current: GhostSheet | None = None  

    try:
        while True:
            text = input("\nyou > ").strip()
            if not text:
                continue

           
            if text.startswith("/"):
                cmd, _, arg = text.partition(" ")  
                cmd, arg = cmd.lower(), arg.strip().lower()

                if cmd == "/quit":
                    print("Your mystery is saved. Come back with the same name to continue.")
                    break

                elif cmd == "/look":
                    for g in ghosts.values():
                        print(f"  {g.room}: {g.name}")

                elif cmd == "/notes":
                    print("\n".join(f"  📓 {c}" for c in notebook) or "  (no clues yet)")
                    print(f"  Wrong guesses left: {MAX_WRONG - wrong}")

                elif cmd == "/go":
                    ghost = rooms.get(arg)
                    if ghost is None:
                        print(f"There's no '{arg}'. Rooms: {', '.join(rooms)}")
                        continue
                    current = ghost
                    key = ghost.name.lower()
                    if key not in histories: 
                        histories[key] = await store.load_history(player, game_id, ghost.name)
                    greeting = f"Oh. YOU again, {player}." if histories[key] else ghost.first_line
                    print(f"\n👻 {ghost.name}: {greeting}")

                elif cmd == "/accuse":
                    if arg == culprit:
                        # ── WIN ──
                        print(f"\n✨ {thief.guilty.confession}")
                        for g in ghosts.values():  
                            if g.name.lower() != culprit:
                                print(f"👻 {g.name}: {g.farewell}")
                        print(f"\n🎃 You solved it! The dentures were in {place}. Grandma smiles. With teeth.")
                        await store.finish_game(player, game_id, culprit)
                        break

                    elif arg in ghosts:
                        
                        wrong += 1
                        await store.add_wrong_guess(player)  
                        print(f"\n👻 {ghosts[arg].name}: {ghosts[arg].outrage}")

                        if wrong >= MAX_WRONG:
                            print("\n💀 The ghosts cackle in unison. Three wrong guesses!")
                            print("   The dentures stay hidden... until next Halloween.")
                            await store.finish_game(player, game_id, culprit)
                            break
                        print(f"   Wrong guesses left: {MAX_WRONG - wrong}")

                    else:
                        print("Accuse whom? Try /look to see the suspects.")

                else:
                    print(HELP)
                continue  
            if current is None:
                print("You're talking to an empty hallway. Try /go <room> first.")
                continue

            key = current.name.lower()
            clues_before = len(notebook)  

            try:
                result = await ghost_agent.run(
                    text, deps=deps_for(current), message_history=histories[key]
                )
            except ModelHTTPError as e:
                if e.status_code == 429:
                    print(f"👻 {current.name} is catching their breath (rate limited). Try again shortly.")
                else:
                    print(f"⚠️  Groq error {e.status_code}: {e.body}")
                continue
            except UnexpectedModelBehavior:
                print(f"👻 {current.name} flickers and mutters something you can't make out.")
                continue

            histories[key] = result.all_messages()
            await store.save_history(player, game_id, current.name, histories[key])
            house.post_gossip(current.name, f'{player} asked {current.name}: "{text[:80]}"')

            out = result.output
            tag = f" [{out.move}]" if DEBUG else ""
            print(f"\n👻 {current.name}{tag}: {out.reply}")
            if out.haunting:
                print(f"   {ITALIC}~ {out.haunting}{RESET}")
            if len(notebook) > clues_before:
                print("   📓 New clue in your notes! (/notes)")
    finally:
        await store.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👻 The house goes quiet...")