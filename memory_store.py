
import os
from datetime import datetime, timezone

from pydantic import ValidationError
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter
from pymongo import AsyncMongoClient
from pymongo.errors import PyMongoError


class MemoryStore:
    """Reads and writes game state and ghost conversations in MongoDB."""

    def __init__(self) -> None:
        
        self._client: AsyncMongoClient | None = None
        self._players = None
        self._conversations = None

    async def connect(self) -> bool:
        """Try to connect. Returns True if long-term memory is available."""
        uri = os.getenv("MONGODB_URI")
        if not uri:
            print("⚠️  MONGODB_URI not set: playing without long-term memory.")
            return False

        client = AsyncMongoClient(uri, serverSelectionTimeoutMS=5000)  # Fail fast: 5 s.
        try:
            await client.admin.command("ping")  # Proves network + login work.
        except PyMongoError as e:
            print(f"⚠️  Can't reach MongoDB ({type(e).__name__}): playing without long-term memory.")
            await client.close()
            return False

        self._client = client
        db = client["screaming_meemies"]  
        self._players = db["players"]
        self._conversations = db["conversations"]
        return True

    async def _update(self, collection, doc_id: str, fields: dict) -> None:
        """Shared helper: set `fields` on one document, creating it if missing.
        One place for the error handling, instead of repeating it in every method."""
        if collection is None:
            return
        try:
            await collection.update_one({"_id": doc_id}, {"$set": fields}, upsert=True)
        except PyMongoError as e:
           
            print(f"⚠️  Couldn't save to MongoDB ({type(e).__name__}).")

  

    async def get_player(self, player: str) -> dict:
        """The player's record, e.g. {"active": {...} or None, "last_culprit": "agnes"}.
        Returns {} for a new player or when there's no database."""
        if self._players is None:
            return {}
        try:
           
            return await self._players.find_one({"_id": player.lower()}) or {}
        except PyMongoError as e:
            print(f"⚠️  Couldn't load player ({type(e).__name__}).")
            return {}

    async def start_game(self, player: str, game_id: str, culprit: str) -> None:
        await self._update(self._players, player.lower(),
                           {"active": {"game_id": game_id, "culprit": culprit}})

    async def finish_game(self, player: str, culprit: str) -> None:
        
        await self._update(self._players, player.lower(),
                           {"active": None, "last_culprit": culprit})

   

    @staticmethod
    def _key(player: str, game_id: str, ghost: str) -> str:
     
        return f"{player.lower()}:{game_id}:{ghost.lower()}"

    async def load_history(self, player: str, game_id: str, ghost: str) -> list[ModelMessage]:
        """Return the saved conversation, or [] if none (or no database)."""
        if self._conversations is None:
            return []
        try:
            doc = await self._conversations.find_one({"_id": self._key(player, game_id, ghost)})
        except PyMongoError as e:
            print(f"⚠️  Couldn't load memory ({type(e).__name__}): starting fresh.")
            return []
        if doc is None:
            return []
        try:
            
            return ModelMessagesTypeAdapter.validate_python(doc["messages"])
        except ValidationError:
            print("⚠️  Saved memory was unreadable: starting fresh.")
            return []

    async def save_history(self, player: str, game_id: str, ghost: str,
                           messages: list[ModelMessage]) -> None:
        await self._update(self._conversations, self._key(player, game_id, ghost), {
            "player": player,
            "game_id": game_id,
            "ghost": ghost,
            
            "messages": ModelMessagesTypeAdapter.dump_python(messages, mode="json"),
            "updated_at": datetime.now(timezone.utc),
        })

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()