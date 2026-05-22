from __future__ import annotations

from typing import Any

from src.core.content import Article, ContentService
from src.core.llm import LLMService
from src.storage.reading_store import ReadingStore
from src.storage.wordbook_store import WordbookStore


class ReadingService:
    def __init__(
        self,
        content: ContentService,
        reading_store: ReadingStore,
        wordbook_store: WordbookStore,
        llm: LLMService,
    ) -> None:
        self._content = content
        self._reading_store = reading_store
        self._wordbook_store = wordbook_store
        self._llm = llm

    async def start_reading(self) -> dict[str, Any]:
        article = await self._content.get_practice_article()
        if not article:
            return {"error": "暂无可用的阅读内容，请稍后再试或输入 /refresh 刷新。"}

        return {
            "title": article.title,
            "url": article.url,
            "source": article.source,
            "content": article.content,
            "word_count": article.word_count,
            "difficulty": article.difficulty,
            "keywords": article.keywords,
            "instructions": self._speed_reading_instructions(),
        }

    async def evaluate_summary(
        self,
        article: Article,
        user_summary: str,
        duration_minutes: float = 0.0,
    ) -> dict[str, Any]:
        evaluation = await self._llm.evaluate_reading(article.content, user_summary)

        await self._reading_store.add_reading(
            source=article.source,
            title=article.title,
            url=article.url,
            content_length=article.word_count,
            difficulty=article.difficulty,
            user_summary=user_summary,
            keywords=article.keywords,
            new_words=evaluation.get("key_words", []),
            duration_minutes=duration_minutes,
        )

        return {
            "accuracy": evaluation.get("accuracy", "unknown"),
            "feedback": evaluation.get("feedback", ""),
            "key_words": evaluation.get("key_words", []),
            "tips": self._reading_tips(),
        }

    async def get_daily_push(self) -> dict[str, Any]:
        daily = await self._content.get_daily_articles()
        result: dict[str, Any] = {}

        if daily["short"]:
            a = daily["short"][0]
            result["short"] = {
                "title": a.title,
                "url": a.url,
                "source": a.source,
                "content": a.content,
                "word_count": a.word_count,
                "difficulty": a.difficulty,
            }

        if daily["medium"]:
            a = daily["medium"][0]
            result["medium"] = {
                "title": a.title,
                "url": a.url,
                "source": a.source,
                "content": a.content,
                "word_count": a.word_count,
                "difficulty": a.difficulty,
            }

        result["instructions"] = self._speed_reading_instructions()
        return result

    def _speed_reading_instructions(self) -> str:
        return (
            "速读三原则：\n"
            "1. 第一遍：完全不查词，快速通读，只抓核心观点（2-3分钟）\n"
            "2. 第二遍：仅查影响理解的关键词，单篇查词不超过3个（1-2分钟）\n"
            "3. 总结：用1句话中文总结大意，不逐句翻译（30秒）\n\n"
            "完成后，请回复你的总结。"
        )

    def _reading_tips(self) -> list[str]:
        return [
            "关注段落首句，快速定位论点",
            "技术文档先看结构（H2/H3标题）",
            "遇到不认识的词，先跳过，不影响理解就不用查",
        ]
