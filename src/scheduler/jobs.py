from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

from src.adapters.feishu.bot import FeishuBot
from src.config.settings import settings
from src.core.reading import ReadingService
from src.core.stats import StatsService


class SchedulerService:
    def __init__(
        self,
        reading: ReadingService,
        stats: StatsService,
        feishu_bot: FeishuBot | None = None,
    ) -> None:
        self._reading = reading
        self._stats = stats
        self._feishu_bot = feishu_bot
        self._scheduler = AsyncIOScheduler()

    def start(self) -> None:
        hour, minute = settings.push_time.split(":")
        self._scheduler.add_job(
            self._daily_push,
            "cron",
            hour=int(hour),
            minute=int(minute),
            id="daily_push",
            replace_existing=True,
        )

        self._scheduler.add_job(
            self._weekly_report,
            "cron",
            day_of_week="sun",
            hour=20,
            minute=0,
            id="weekly_report",
            replace_existing=True,
        )

        self._scheduler.start()
        logger.info("Scheduler started: daily_push at {}, weekly_report on Sunday 20:00", settings.push_time)

    def shutdown(self) -> None:
        self._scheduler.shutdown()

    async def _daily_push(self) -> None:
        logger.info("Running daily push job")
        try:
            push_data = await self._reading.get_daily_push()
            if not push_data:
                logger.warning("No articles for daily push")
                return

            text_parts = ["☀️ 每日英文阅读推送\n"]

            if "short" in push_data:
                s = push_data["short"]
                text_parts.append(
                    f"【短篇】{s['title']}\n"
                    f"来源: {s['source']} | 字数: {s['word_count']}\n"
                    f"{s['content']}\n"
                )

            if "medium" in push_data:
                m = push_data["medium"]
                text_parts.append(
                    f"【中篇】{m['title']}\n"
                    f"来源: {m['source']} | 字数: {m['word_count']}\n"
                    f"{m['content']}\n"
                )

            if "instructions" in push_data:
                text_parts.append(f"---\n{push_data['instructions']}")

            text = "\n".join(text_parts)

            if self._feishu_bot:
                await self._feishu_bot.send_to_user("default", text)

        except Exception as e:
            logger.error("daily_push failed: {}", e)

    async def _weekly_report(self) -> None:
        logger.info("Running weekly report job")
        try:
            report = await self._stats.generate_weekly_report()

            if self._feishu_bot:
                await self._feishu_bot.send_to_user("default", report)

        except Exception as e:
            logger.error("weekly_report failed: {}", e)
