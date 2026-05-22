from __future__ import annotations

from typing import Any

from src.core.llm import LLMService
from src.storage.wordbook_store import WordbookStore


class WordbookService:
    def __init__(self, store: WordbookStore, llm: LLMService) -> None:
        self._store = store
        self._llm = llm

    async def add_new_word(
        self,
        word: str,
        context: str = "",
    ) -> dict[str, Any]:
        definition_data = await self._llm.generate_definition(word, context)

        record_id = await self._store.add_word(
            word=word,
            definition=definition_data.get("definition", ""),
            example=definition_data.get("example", ""),
            example_source=definition_data.get("example_source", ""),
            source="对话",
            difficulty=definition_data.get("difficulty", "中级"),
            tags=definition_data.get("tags", []),
        )

        return {
            "word": word,
            "definition": definition_data.get("definition", ""),
            "example": definition_data.get("example", ""),
            "example_source": definition_data.get("example_source", ""),
            "tags": definition_data.get("tags", []),
            "difficulty": definition_data.get("difficulty", "中级"),
            "added": record_id is not None,
        }

    async def lookup_word(self, word: str) -> dict[str, Any]:
        existing = await self._store.get_word(word)
        if existing:
            fields = existing["fields"]
            return {
                "word": word,
                "definition": fields.get("definition", ""),
                "example": fields.get("example", ""),
                "example_source": fields.get("example_source", ""),
                "tags": [t.strip() for t in fields.get("tags", "").split(",") if t.strip()],
                "difficulty": fields.get("difficulty", ""),
                "in_wordbook": True,
            }

        definition_data = await self._llm.generate_definition(word)

        record_id = await self._store.add_word(
            word=word,
            definition=definition_data.get("definition", ""),
            example=definition_data.get("example", ""),
            example_source=definition_data.get("example_source", ""),
            source="查词",
            difficulty=definition_data.get("difficulty", "中级"),
            tags=definition_data.get("tags", []),
        )

        return {
            "word": word,
            "definition": definition_data.get("definition", ""),
            "example": definition_data.get("example", ""),
            "example_source": definition_data.get("example_source", ""),
            "tags": definition_data.get("tags", []),
            "difficulty": definition_data.get("difficulty", "中级"),
            "in_wordbook": False,
            "auto_added": record_id is not None,
        }

    async def get_wordbook_status(self) -> dict[str, Any]:
        return await self._store.get_stats()
