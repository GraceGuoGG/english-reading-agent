from __future__ import annotations

import json
from pathlib import Path

from loguru import logger
from openai import AsyncOpenAI

from src.config.settings import settings

PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "config" / "prompts"


def _load_prompt(name: str) -> str:
    path = PROMPTS_DIR / f"{name}.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    logger.warning("Prompt file not found: {}", path)
    return ""


class LLMService:
    def __init__(self) -> None:
        self._client: AsyncOpenAI | None = None
        self._model = settings.doubao_model
        self._prompts: dict[str, str] = {}

    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            api_key = settings.doubao_api_key or "placeholder"
            self._client = AsyncOpenAI(
                api_key=api_key,
                base_url=settings.doubao_base_url,
            )
        return self._client

    def _get_prompt(self, name: str) -> str:
        if name not in self._prompts:
            self._prompts[name] = _load_prompt(name)
        return self._prompts[name]

    async def chat(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        try:
            resp = await self._get_client().chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return resp.choices[0].message.content or ""
        except Exception as e:
            logger.error("LLM chat failed: {}", e)
            return ""

    async def recognize_intent(self, message: str) -> dict:
        prompt = self._get_prompt("intent")
        if not prompt:
            return self._fallback_intent(message)

        result = await self.chat(prompt, message, temperature=0.1)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return self._fallback_intent(message)

    def _fallback_intent(self, message: str) -> dict:
        msg = message.strip().lower()
        if msg.startswith("/english") or "开始学习" in msg:
            return {"intent": "start_reading", "args": ""}
        if msg.startswith("/review") or "复习单词" in msg or "复习专业词汇" in msg:
            return {"intent": "review", "args": ""}
        if msg.startswith("/wordbook") or "查看单词本" in msg:
            return {"intent": "wordbook", "args": ""}
        if msg.startswith("/stats") or "学习统计" in msg:
            return {"intent": "stats", "args": ""}
        if msg.startswith("/help") or "帮助" in msg:
            return {"intent": "help", "args": ""}
        if msg.startswith("/refresh") or "刷新推送" in msg:
            return {"intent": "refresh", "args": ""}
        if msg.startswith("/export") or "导出单词本" in msg:
            return {"intent": "export", "args": ""}
        if msg.startswith("/settings") or "设置" in msg:
            return {"intent": "settings", "args": ""}
        if msg.startswith("拆解") or "帮我拆解这句话" in msg:
            sentence = message
            if msg.startswith("拆解"):
                sentence = message[2:].strip()
            return {"intent": "parse_sentence", "args": sentence}
        if "是什么意思" in msg:
            word = message.replace("是什么意思", "").strip()
            return {"intent": "lookup", "args": word}
        if len(message.split()) <= 3 and message.isascii():
            return {"intent": "lookup", "args": message.strip()}
        return {"intent": "chat", "args": message}

    async def generate_definition(self, word: str, context: str = "") -> dict:
        prompt = self._get_prompt("definition")
        if not prompt:
            return {"definition": "", "example": "", "example_source": "", "tags": [], "difficulty": "中级"}

        user_msg = f"单词: {word}"
        if context:
            user_msg += f"\n上下文: {context}"

        result = await self.chat(prompt, user_msg, temperature=0.3)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"definition": result, "example": "", "example_source": "", "tags": [], "difficulty": "中级"}

    async def parse_long_sentence(self, sentence: str) -> dict:
        prompt = self._get_prompt("sentence_parse")
        if not prompt:
            return {"main_clause": "", "tech_components": [], "simplified": ""}

        result = await self.chat(prompt, sentence, temperature=0.3)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"main_clause": "", "tech_components": [], "simplified": result}

    async def evaluate_reading(self, article: str, user_summary: str) -> dict:
        prompt = self._get_prompt("reading_eval")
        if not prompt:
            return {"accuracy": "unknown", "feedback": "", "key_words": []}

        user_msg = f"原文:\n{article}\n\n用户总结:\n{user_summary}"
        result = await self.chat(prompt, user_msg, temperature=0.3)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"accuracy": "unknown", "feedback": result, "key_words": []}

    async def generate_weekly_report(self, stats: dict) -> str:
        prompt = self._get_prompt("weekly_report")
        if not prompt:
            return "周报生成失败"

        import json as _json
        user_msg = f"本周学习数据:\n{_json.dumps(stats, ensure_ascii=False, indent=2)}"
        return await self.chat(prompt, user_msg, temperature=0.5)
