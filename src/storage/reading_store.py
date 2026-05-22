from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from src.config.settings import settings
from src.storage.bitable import BitableStore


class ReadingStore:
    def __init__(self, store: BitableStore) -> None:
        self._store = store
        self._table_id = settings.bitable_reading_table_id

    async def add_reading(
        self,
        source: str,
        title: str,
        url: str,
        content_length: int,
        difficulty: str,
        user_summary: str = "",
        keywords: list[str] | None = None,
        new_words: list[str] | None = None,
        duration_minutes: float = 0.0,
    ) -> str | None:
        fields: dict[str, Any] = {
            "source": source,
            "title": title,
            "url": url,
            "content_length": content_length,
            "difficulty": difficulty,
            "read_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "duration_minutes": duration_minutes,
            "user_summary": user_summary,
            "keywords_encountered": ", ".join(keywords or []),
            "new_words_added": ", ".join(new_words or []),
        }
        return await self._store.create_record(self._table_id, fields)

    async def update_reading(self, record_id: str, fields: dict[str, Any]) -> bool:
        return await self._store.update_record(self._table_id, record_id, fields)

    async def list_readings(self, days: int | None = None) -> list[dict[str, Any]]:
        filter_expr = None
        if days:
            since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            filter_expr = f'CurrentValue.[read_at] >= "{since}"'

        return await self._store.list_records(self._table_id, filter_expr=filter_expr)

    async def get_stats(self, days: int = 7) -> dict[str, Any]:
        readings = await self.list_readings(days=days)
        total = len(readings)

        if total == 0:
            return {
                "period_days": days,
                "total_readings": 0,
                "avg_duration": 0.0,
                "new_words_count": 0,
                "by_difficulty": {},
                "by_source": {},
            }

        total_duration = sum(r["fields"].get("duration_minutes", 0) for r in readings)
        all_new_words: list[str] = []
        by_difficulty: dict[str, int] = {}
        by_source: dict[str, int] = {}

        for r in readings:
            f = r["fields"]
            diff = f.get("difficulty", "未知")
            src = f.get("source", "未知")
            by_difficulty[diff] = by_difficulty.get(diff, 0) + 1
            by_source[src] = by_source.get(src, 0) + 1

            nw = f.get("new_words_added", "")
            if nw:
                all_new_words.extend(w.strip() for w in nw.split(",") if w.strip())

        return {
            "period_days": days,
            "total_readings": total,
            "avg_duration": round(total_duration / total, 1),
            "new_words_count": len(all_new_words),
            "by_difficulty": by_difficulty,
            "by_source": by_source,
        }

    async def get_today_count(self) -> int:
        today = datetime.now().strftime("%Y-%m-%d")
        readings = await self._store.list_records(
            self._table_id,
            filter_expr=f'CurrentValue.[read_at] >= "{today}"',
        )
        return len(readings)
