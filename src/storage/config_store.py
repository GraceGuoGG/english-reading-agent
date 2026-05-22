from __future__ import annotations

from typing import Any

from src.config.settings import settings
from src.storage.bitable import BitableStore


class ConfigStore:
    def __init__(self, store: BitableStore) -> None:
        self._store = store
        self._table_id = settings.bitable_config_table_id

    async def get_config(self, user_id: str = "default") -> dict[str, Any]:
        records = await self._store.list_records(
            self._table_id,
            filter_expr=f'CurrentValue.[user_id] = "{user_id}"',
        )

        if records:
            return records[0]["fields"]

        default_config: dict[str, Any] = {
            "user_id": user_id,
            "preferred_push_time": settings.push_time,
            "daily_short_article_count": settings.daily_short_count,
            "daily_medium_article_count": settings.daily_medium_count,
            "difficulty_preference": "自适应",
            "github_sources": "blog, readme",
            "reddit_subreddits": "",
        }
        await self._store.create_record(self._table_id, default_config)
        return default_config

    async def update_config(self, user_id: str = "default", **kwargs: Any) -> bool:
        records = await self._store.list_records(
            self._table_id,
            filter_expr=f'CurrentValue.[user_id] = "{user_id}"',
        )

        if not records:
            config = await self.get_config(user_id)
            config.update(kwargs)
            await self._store.create_record(self._table_id, config)
            return True

        return await self._store.update_record(
            self._table_id,
            records[0]["record_id"],
            kwargs,
        )
