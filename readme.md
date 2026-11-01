# Screaming Meemies

It's 8 AM on Halloween. Grandma smiles at you and she has no teeth. Her dentures
went missing overnight, and the ghosts living in her house know who took them.

I built this for the Hacktoberfest 2026 DEV challenge (Ghost in the Machine).
It's a mystery game you play in the terminal. Each ghost is its own AI agent
with its own personality, secret, cover story and memory. They gossip about
you, whisper to each other to keep their stories straight, mess with your
reality a little, and only give you clues if you earn them. The thief is
different every game, so you can't just remember the answer.

The idea came from The Haunting of Hill House. I love how the ghosts there are
tied to the family's past and show up in ways that make you question what you
just saw. I wanted that feeling but funny instead of sad, so here the ghosts are
a petty housekeeper, a sarcastic gardener, a snobby butler and a great-great-aunt
who just wants candy.

## How it works

The ghosts run on Qwen, an open-weight model, served through Groq. I used
PydanticAI for the agents, so every ghost reply comes back in a fixed format
(what the ghost decides to do, what it says, and an optional haunting), and bad
replies get retried automatically.

Ghosts talk to each other through the house. When you question one ghost, the
others overhear it. A ghost can also secretly whisper to another ghost, for
example to ask for an alibi.

Games are saved in MongoDB Atlas, so you can quit and come back to the same
mystery with the same thief and the same number of guesses left.

If the thief accidentally says where the dentures are hidden, a checker catches
it and makes the ghost rewrite its reply before you ever see it. Every catch is
logged in Sentry, along with traces of each ghost's turn.

## How to run it

You need Python 3.10 or newer.

```bash
pip install -r requirements.txt
```

Make a `.env` file with your keys:

```bash
GROQ_API_KEY=...       # free at console.groq.com
MONGODB_URI=...        # optional, free cluster at mongodb.com/atlas
SENTRY_DSN=...         # optional, free at sentry.io
PYDANTIC_AI_NO_BANNER=1
```

Then:

```bash
python game.py
```

Run `DEBUG=1 python game.py` if you want to see what each ghost is secretly
deciding (lie, deflect, reveal or whisper).

The game still works without MongoDB or Sentry, it just won't save your game
or record traces.

## How to play

Type `/look` to see the rooms, then `/go kitchen` (or garden, dining room,
attic) to visit a ghost. Anything you type that doesn't start with `/` is said
to the ghost in the room. `/notes` shows your clues. When you think you know,
type `/accuse <ghost>`. You get three wrong guesses before the ghosts win.

## Files

- `game.py` is the game itself
- `ghost_agent.py` is the ghost brain (instructions, tools, leak check)
- `ghosts/` has the four ghosts, each with a guilty and an innocent version
- `ghosts.py` checks that the ghost files are filled in correctly
- `house.py` handles gossip and whispers
- `memory_store.py` saves games to MongoDB
- `checker.py` catches leaks and reports them to Sentry
- `observability.py` sets up Sentry

## Things I'd still like to add

The leak checker only catches the hiding place by name, not hints around it.
I'd like to add a proper fact checker. Right now ghosts only act when you talk
to them, and gossip resets when you quit. I'd also like to make each ghost its
own A2A agent someday.

## A note on privacy

If Sentry is on, conversations (including the name you type) are recorded so
I can debug the ghosts. Leave `SENTRY_DSN` empty if you don't want that.

## Credits

- Qwen (open-weight model, [license here]) served by Groq
- PydanticAI for the agents
- MongoDB Atlas and Sentry
- Inspired by The Haunting of Hill House (no characters or story used) for the Halloween theme!

## License

MIT
