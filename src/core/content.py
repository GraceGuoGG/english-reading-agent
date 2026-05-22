from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import feedparser
import httpx
from loguru import logger

from src.config.settings import settings

KEYWORD_WHITELIST = [
    "llm", "agent", "ai", "product", "api", "integration",
    "model", "prompt", "copilot", "gpt", "openai", "claude",
    "machine learning", "deep learning", "neural", "transformer",
    "fine-tun", "inference", "rag", "embedding", "vector",
    "deployment", "microservice", "middleware", "orchestration",
    "container", "kubernetes", "devops", "mlops",
]

KEYWORD_BLACKLIST = [
    "hiring", "job", "career", "recruit", "salary",
    "advertisement", "sponsor", "promo",
]


@dataclass
class Article:
    title: str
    url: str
    content: str
    source: str
    published: str = ""
    word_count: int = 0
    difficulty: str = "中级"
    keywords: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.word_count = len(self.content.split())
        self.difficulty = self._estimate_difficulty()

    def _estimate_difficulty(self) -> str:
        if self.word_count <= 100:
            return "初级"
        if self.word_count <= 300:
            return "中级"
        return "高级"


class ContentService:
    def __init__(self) -> None:
        self._feeds = settings.rss_feed_list
        self._cache: list[Article] = []
        self._last_fetch: datetime | None = None

    async def fetch_articles(self, force: bool = False) -> list[Article]:
        if not force and self._cache and self._last_fetch:
            elapsed = (datetime.now() - self._last_fetch).total_seconds()
            if elapsed < 3600:
                return self._cache

        articles: list[Article] = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            for feed_url in self._feeds:
                try:
                    resp = await client.get(feed_url)
                    resp.raise_for_status()
                    feed = feedparser.parse(resp.text)

                    for entry in feed.entries[:20]:
                        content = self._extract_content(entry)
                        article = Article(
                            title=entry.get("title", ""),
                            url=entry.get("link", ""),
                            content=content,
                            source=self._extract_source(feed_url),
                            published=entry.get("published", ""),
                        )
                        articles.append(article)
                except Exception as e:
                    logger.error("Failed to fetch {}: {}", feed_url, e)

        filtered = self._filter_articles(articles)
        self._cache = filtered
        self._last_fetch = datetime.now()
        return filtered

    async def get_daily_articles(self) -> dict[str, list[Article]]:
        articles = await self.fetch_articles()
        short = [a for a in articles if a.word_count <= 100]
        medium = [a for a in articles if 100 < a.word_count <= 300]

        short_pick = short[:settings.daily_short_count]
        medium_pick = medium[:settings.daily_medium_count]

        return {"short": short_pick, "medium": medium_pick}

    async def get_practice_article(self) -> Article | None:
        articles = await self.fetch_articles()
        short = [a for a in articles if a.word_count <= 100]
        if short:
            import random
            return random.choice(short)
        return articles[0] if articles else None

    def _extract_content(self, entry: Any) -> str:
        if hasattr(entry, "summary"):
            text = re.sub(r"<[^>]+>", "", entry.summary)
            return text.strip()
        if hasattr(entry, "content") and entry.content:
            text = re.sub(r"<[^>]+>", "", entry.content[0].get("value", ""))
            return text.strip()
        return ""

    def _extract_source(self, feed_url: str) -> str:
        if "github.blog" in feed_url:
            return "GitHub Blog"
        if "github.com" in feed_url:
            return "GitHub"
        return "RSS"

    def _filter_articles(self, articles: list[Article]) -> list[Article]:
        result: list[Article] = []
        for article in articles:
            text_lower = (article.title + " " + article.content).lower()

            has_blacklist = any(kw in text_lower for kw in KEYWORD_BLACKLIST)
            if has_blacklist:
                continue

            has_whitelist = any(kw in text_lower for kw in KEYWORD_WHITELIST)
            if has_whitelist:
                article.keywords = [
                    kw for kw in KEYWORD_WHITELIST if kw in text_lower
                ]
                result.append(article)

        return result
