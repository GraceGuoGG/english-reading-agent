from __future__ import annotations

from datetime import datetime
from typing import Any

from src.config.settings import settings
from src.storage.bitable import BitableStore


class WordbookStore:
    def __init__(self, store: BitableStore) -> None:
        self._store = store
        self._table_id = settings.bitable_wordbook_table_id

    async def add_word(
        self,
        word: str,
        definition: str,
        example: str,
        example_source: str,
        source: str,
        difficulty: str,
        tags: list[str],
    ) -> str | None:
        existing = await self.get_word(word)
        if existing:
            fields = {
                "frequency": existing["fields"].get("frequency", 0) + 1,
            }
            await self._store.update_record(self._table_id, existing["record_id"], fields)
            return existing["record_id"]

        fields: dict[str, Any] = {
            "word": word,
            "definition": definition,
            "example": example,
            "example_source": example_source,
            "source": source,
            "difficulty": difficulty,
            "frequency": 1,
            "review_count": 0,
            "correct_count": 0,
            "tags": ", ".join(tags),
            "status": "学习中",
            "added_at": datetime.now().strftime("%Y-%m-%d"),
            "last_reviewed_at": "",
            "consecutive_correct": 0,
        }
        return await self._store.create_record(self._table_id, fields)

    async def get_word(self, word: str) -> dict[str, Any] | None:
        records = await self._store.list_records(
            self._table_id,
            filter_expr=f'CurrentValue.[word] = "{word}"',
        )
        return records[0] if records else None

    async def list_words(
        self,
        status: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        filter_expr = None
        if status:
            filter_expr = f'CurrentValue.[status] = "{status}"'

        records = await self._store.list_records(self._table_id, filter_expr=filter_expr)
        if limit:
            records = records[:limit]
        return records

    async def update_review(self, word: str, correct: bool) -> dict[str, Any] | None:
        record = await self.get_word(word)
        if not record:
            return None

        fields = record["fields"]
        review_count = fields.get("review_count", 0) + 1
        correct_count = fields.get("correct_count", 0) + (1 if correct else 0)
        consecutive = fields.get("consecutive_correct", 0)
        consecutive = consecutive + 1 if correct else 0

        update_fields: dict[str, Any] = {
            "review_count": review_count,
            "correct_count": correct_count,
            "consecutive_correct": consecutive,
            "last_reviewed_at": datetime.now().strftime("%Y-%m-%d"),
        }

        if consecutive >= 3:
            update_fields["status"] = "已淘汰"

        await self._store.update_record(self._table_id, record["record_id"], update_fields)
        return {"word": word, "eliminated": consecutive >= 3}

    async def get_review_candidates(self, count: int = 10) -> list[dict[str, Any]]:
        records = await self.list_words(status="学习中")
        import random
        random.shuffle(records)
        return records[:count]

    async def get_stats(self) -> dict[str, Any]:
        all_words = await self._store.list_records(self._table_id)
        total = len(all_words)
        learning = sum(1 for r in all_words if r["fields"].get("status") == "学习中")
        eliminated = sum(1 for r in all_words if r["fields"].get("status") == "已淘汰")

        recent = sorted(
            all_words,
            key=lambda r: r["fields"].get("added_at", ""),
            reverse=True,
        )[:5]

        return {
            "total": total,
            "learning": learning,
            "eliminated": eliminated,
            "recent_words": [
                {
                    "word": r["fields"].get("word", ""),
                    "tags": r["fields"].get("tags", ""),
                    "added_at": r["fields"].get("added_at", ""),
                }
                for r in recent
            ],
        }

    async def eliminate_word(self, word: str) -> bool:
        record = await self.get_word(word)
        if not record:
            return False
        return await self._store.update_record(
            self._table_id,
            record["record_id"],
            {"status": "已淘汰", "consecutive_correct": 3},
        )
