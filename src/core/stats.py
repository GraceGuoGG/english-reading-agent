from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from src.core.llm import LLMService
from src.storage.reading_store import ReadingStore
from src.storage.wordbook_store import WordbookStore


class StatsService:
    def __init__(
        self,
        wordbook_store: WordbookStore,
        reading_store: ReadingStore,
        llm: LLMService,
    ) -> None:
        self._wordbook_store = wordbook_store
        self._reading_store = reading_store
        self._llm = llm

    async def get_daily_stats(self) -> dict[str, Any]:
        reading_stats = await self._reading_store.get_stats(days=1)
        wordbook_stats = await self._wordbook_store.get_stats()

        return {
            "today_readings": reading_stats.get("total_readings", 0),
            "wordbook_total": wordbook_stats.get("total", 0),
            "wordbook_learning": wordbook_stats.get("learning", 0),
            "wordbook_eliminated": wordbook_stats.get("eliminated", 0),
        }

    async def generate_weekly_report(self) -> str:
        reading_stats = await self._reading_store.get_stats(days=7)
        wordbook_stats = await self._wordbook_store.get_stats()

        all_words = await self._wordbook_store.list_words(status="学习中")
        total_reviews = sum(w["fields"].get("review_count", 0) for w in all_words)
        total_correct = sum(w["fields"].get("correct_count", 0) for w in all_words)
        accuracy = round(total_correct / total_reviews * 100, 1) if total_reviews > 0 else 0

        eliminated_this_week = 0
        now = datetime.now()
        week_ago = now - timedelta(days=7)
        for w in all_words:
            last_reviewed = w["fields"].get("last_reviewed_at", "")
            if last_reviewed and last_reviewed >= week_ago.strftime("%Y-%m-%d"):
                if w["fields"].get("consecutive_correct", 0) >= 3:
                    eliminated_this_week += 1

        stats = {
            "reading": reading_stats,
            "wordbook": {
                "total": wordbook_stats.get("total", 0),
                "learning": wordbook_stats.get("learning", 0),
                "eliminated": wordbook_stats.get("eliminated", 0),
                "eliminated_this_week": eliminated_this_week,
                "review_accuracy": accuracy,
            },
        }

        return await self._llm.generate_weekly_report(stats)

    async def get_stats_overview(self) -> dict[str, Any]:
        reading_stats = await self._reading_store.get_stats(days=7)
        wordbook_stats = await self._wordbook_store.get_stats()
        today_count = await self._reading_store.get_today_count()

        return {
            "today_readings": today_count,
            "weekly_readings": reading_stats.get("total_readings", 0),
            "weekly_avg_duration": reading_stats.get("avg_duration", 0),
            "wordbook_total": wordbook_stats.get("total", 0),
            "wordbook_learning": wordbook_stats.get("learning", 0),
            "wordbook_eliminated": wordbook_stats.get("eliminated", 0),
        }
