from __future__ import annotations

from typing import Any

from src.core.llm import LLMService


class SentenceService:
    def __init__(self, llm: LLMService) -> None:
        self._llm = llm

    async def parse_sentence(self, sentence: str) -> dict[str, Any]:
        result = await self._llm.parse_long_sentence(sentence)

        return {
            "original": sentence,
            "main_clause": result.get("main_clause", ""),
            "tech_components": result.get("tech_components", []),
            "simplified": result.get("simplified", ""),
        }
