from __future__ import annotations

from typing import Any

from src.core.llm import LLMService
from src.storage.wordbook_store import WordbookStore


class ReviewService:
    def __init__(self, store: WordbookStore, llm: LLMService) -> None:
        self._store = store
        self._llm = llm

    async def generate_quiz(self, count: int = 10) -> dict[str, Any]:
        candidates = await self._store.get_review_candidates(count)
        if not candidates:
            return {"words": [], "message": "单词本中没有待复习的单词，继续阅读积累新词吧。"}

        quiz_words = []
        for r in candidates:
            fields = r["fields"]
            quiz_words.append({
                "word": fields.get("word", ""),
                "definition": fields.get("definition", ""),
                "example": fields.get("example", ""),
                "tags": fields.get("tags", ""),
            })

        return {"words": quiz_words, "total": len(quiz_words)}

    async def evaluate_answers(
        self,
        answers: dict[str, str],
        quiz_words: list[dict[str, Any]],
    ) -> dict[str, Any]:
        results: list[dict[str, Any]] = []
        eliminated_words: list[str] = []

        for i, word_info in enumerate(quiz_words):
            word = word_info["word"]
            user_answer = answers.get(str(i + 1), "").strip()
            standard_def = word_info["definition"]

            is_correct = self._check_answer(user_answer, standard_def)

            review_result = await self._store.update_review(word, is_correct)

            result = {
                "index": i + 1,
                "word": word,
                "user_answer": user_answer,
                "standard_definition": standard_def,
                "example": word_info.get("example", ""),
                "correct": is_correct,
            }

            if review_result and review_result.get("eliminated"):
                eliminated_words.append(word)

            results.append(result)

        correct_count = sum(1 for r in results if r["correct"])
        total = len(results)

        return {
            "results": results,
            "correct_count": correct_count,
            "total": total,
            "accuracy": round(correct_count / total * 100, 1) if total > 0 else 0,
            "eliminated_words": eliminated_words,
        }

    def _check_answer(self, user_answer: str, standard_definition: str) -> bool:
        if not user_answer:
            return False

        user_lower = user_answer.lower()
        standard_lower = standard_definition.lower()

        key_terms = [t.strip() for t in standard_lower.split("；") if t.strip()]
        if not key_terms:
            key_terms = [standard_lower]

        matched = sum(1 for term in key_terms if term in user_lower)
        return matched > 0
