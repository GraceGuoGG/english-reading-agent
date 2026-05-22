from __future__ import annotations

import asyncio
import json
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from src.config.settings import settings
from src.storage.bitable import BitableStore
from src.storage.wordbook_store import WordbookStore
from src.storage.reading_store import ReadingStore
from src.core.llm import LLMService
from src.core.wordbook import WordbookService
from src.core.review import ReviewService
from src.core.content import ContentService
from src.core.reading import ReadingService
from src.core.sentence import SentenceService
from src.core.stats import StatsService


app = Server("english-reading-coach")

_services: dict[str, Any] = {}
_active_quiz: dict[str, list[dict[str, Any]]] = {}


def _get_services() -> dict[str, Any]:
    if not _services:
        bitable = BitableStore()
        wordbook_store = WordbookStore(bitable)
        reading_store = ReadingStore(bitable)
        llm = LLMService()
        wordbook = WordbookService(wordbook_store, llm)
        review = ReviewService(wordbook_store, llm)
        content = ContentService()
        reading = ReadingService(content, reading_store, wordbook_store, llm)
        sentence = SentenceService(llm)
        stats = StatsService(wordbook_store, reading_store, llm)

        _services["wordbook"] = wordbook
        _services["review"] = review
        _services["content"] = content
        _services["reading"] = reading
        _services["sentence"] = sentence
        _services["stats"] = stats
        _services["wordbook_store"] = wordbook_store
        _services["reading_store"] = reading_store

    return _services


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="lookup_word",
            description="查询单词的AI/技术场景释义，自动加入单词本。输入：单词",
            inputSchema={
                "type": "object",
                "properties": {
                    "word": {"type": "string", "description": "要查询的英文单词"}
                },
                "required": ["word"],
            },
        ),
        Tool(
            name="start_reading",
            description="开始今日阅读训练，返回一篇技术文章和速读指引",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="evaluate_reading",
            description="评估用户的阅读理解总结。输入：用户总结",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_summary": {"type": "string", "description": "用户的中文总结"}
                },
                "required": ["user_summary"],
            },
        ),
        Tool(
            name="start_review",
            description="启动单词复习考核，从单词本抽取10个词出题",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="submit_review",
            description="提交复习答案并获取判分结果。输入：答案字典，如 {\"1\": \"集成\", \"2\": \"编排\"}",
            inputSchema={
                "type": "object",
                "properties": {
                    "answers": {
                        "type": "string",
                        "description": "答案，格式：序号.答案 用空格分隔，如 1.集成 2.编排"
                    }
                },
                "required": ["answers"],
            },
        ),
        Tool(
            name="parse_sentence",
            description="拆解英文长难句，提取主干+标注技术成分+给简化理解",
            inputSchema={
                "type": "object",
                "properties": {
                    "sentence": {"type": "string", "description": "要拆解的英文长难句"}
                },
                "required": ["sentence"],
            },
        ),
        Tool(
            name="get_stats",
            description="查看学习统计，包括阅读进度和单词本状态",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="get_wordbook",
            description="查看单词本状态，包括总词汇量、学习中、已淘汰、最近录入",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="refresh_content",
            description="手动刷新内容，重新抓取GitHub RSS文章",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    svc = _get_services()

    if name == "lookup_word":
        word = arguments.get("word", "")
        if not word:
            return [TextContent(type="text", text="请输入要查询的单词。")]
        result = await svc["wordbook"].lookup_word(word)
        lines = [
            f"📖 {result['word']}\n",
            f"【AI/技术场景释义】\n{result['definition']}\n",
            f"【典型例句】\n{result['example']}",
        ]
        if result.get("example_source"):
            lines.append(f"— {result['example_source']}")
        if result.get("tags"):
            lines.append(f"\n【标签】{' | '.join(result['tags'])}")
        lines.append(f"\n【难度】{result.get('difficulty', '中级')}")
        if result.get("auto_added"):
            lines.append("\n【已加入单词本 ✅】")
        elif result.get("in_wordbook"):
            lines.append("\n【已在单词本中 ✅】")
        return [TextContent(type="text", text="\n".join(lines))]

    elif name == "start_reading":
        result = await svc["reading"].start_reading()
        if "error" in result:
            return [TextContent(type="text", text=result["error"])]
        text = (
            f"📖 今日阅读训练\n\n"
            f"【{result['title']}】\n"
            f"来源: {result['source']} | 字数: {result['word_count']} | 难度: {result['difficulty']}\n"
            f"链接: {result['url']}\n\n"
            f"{result['content']}\n\n"
            f"---\n{result['instructions']}"
        )
        return [TextContent(type="text", text=text)]

    elif name == "evaluate_reading":
        user_summary = arguments.get("user_summary", "")
        if not user_summary:
            return [TextContent(type="text", text="请输入你的阅读总结。")]
        reading_svc = svc["reading"]
        article_result = await reading_svc.start_reading()
        if "error" in article_result:
            return [TextContent(type="text", text="无法获取文章进行评估。")]
        from src.core.content import Article
        article = Article(
            title=article_result["title"],
            url=article_result["url"],
            content=article_result["content"],
            source=article_result["source"],
            word_count=article_result["word_count"],
            difficulty=article_result["difficulty"],
            keywords=article_result.get("keywords", []),
        )
        result = await reading_svc.evaluate_summary(article, user_summary)
        lines = [
            "✅ 阅读完成\n",
            f"【理解评估】\n准确度: {result['accuracy']}",
        ]
        if result.get("feedback"):
            lines.append(f"反馈: {result['feedback']}")
        if result.get("key_words"):
            lines.append(f"\n【需掌握的技术词】")
            for w in result["key_words"]:
                lines.append(f"• {w}")
        return [TextContent(type="text", text="\n".join(lines))]

    elif name == "start_review":
        quiz = await svc["review"].generate_quiz()
        if not quiz["words"]:
            return [TextContent(type="text", text=quiz.get("message", "单词本中没有待复习的单词。"))]
        _active_quiz["default"] = quiz["words"]
        lines = [f"📝 专业词汇复习 (1/{quiz['total']})\n"]
        for i, w in enumerate(quiz["words"], 1):
            lines.append(f"{i}. {w['word']}: ____________")
        lines.append("\n请回复你的答案，格式：1.xxx 2.xxx ...")
        return [TextContent(type="text", text="\n".join(lines))]

    elif name == "submit_review":
        answers_str = arguments.get("answers", "")
        quiz_words = _active_quiz.get("default", [])
        if not quiz_words:
            return [TextContent(type="text", text="没有进行中的复习，请先输入 /review 开始。")]
        answers: dict[str, str] = {}
        for part in answers_str.strip().split():
            if "." in part:
                idx, _, ans = part.partition(".")
                if idx.isdigit():
                    answers[idx] = ans
        if not answers:
            return [TextContent(type="text", text="无法解析答案，请使用格式：1.集成 2.编排")]
        result = await svc["review"].evaluate_answers(answers, quiz_words)
        _active_quiz.pop("default", None)
        lines = []
        for r in result["results"]:
            if r["correct"]:
                lines.append(f"✅ 第{r['index']}题正确\n   {r['word']}: {r['standard_definition']}")
            else:
                lines.append(
                    f"❌ 第{r['index']}题错误\n"
                    f"   你的答案: {r['user_answer']}\n"
                    f"   标准答案: {r['standard_definition']}"
                )
                if r.get("example"):
                    lines.append(f"   例句: {r['example']}")
        lines.append(f"\n📊 正确率: {result['accuracy']}% ({result['correct_count']}/{result['total']})")
        if result.get("eliminated_words"):
            lines.append(f"\n🎉 已淘汰: {', '.join(result['eliminated_words'])}")
        return [TextContent(type="text", text="\n".join(lines))]

    elif name == "parse_sentence":
        sentence = arguments.get("sentence", "")
        if not sentence:
            return [TextContent(type="text", text="请输入要拆解的句子。")]
        result = await svc["sentence"].parse_sentence(sentence)
        lines = [
            "🔍 长难句拆解\n",
            f"原句: {result['original']}\n",
            f"【主干】\n{result['main_clause']}\n",
            "【技术成分】",
        ]
        for comp in result.get("tech_components", []):
            if isinstance(comp, dict):
                lines.append(f"• {comp.get('term', '')} - {comp.get('meaning', '')}")
            else:
                lines.append(f"• {comp}")
        lines.append(f"\n【简化理解】\n{result['simplified']}")
        return [TextContent(type="text", text="\n".join(lines))]

    elif name == "get_stats":
        result = await svc["stats"].get_stats_overview()
        text = (
            f"📊 学习统计\n\n"
            f"今日阅读: {result['today_readings']} 篇\n"
            f"本周阅读: {result['weekly_readings']} 篇\n"
            f"本周平均阅读时长: {result['weekly_avg_duration']} 分钟/篇\n\n"
            f"单词本总量: {result['wordbook_total']}\n"
            f"学习中: {result['wordbook_learning']}\n"
            f"已淘汰: {result['wordbook_eliminated']}"
        )
        return [TextContent(type="text", text=text)]

    elif name == "get_wordbook":
        result = await svc["wordbook"].get_wordbook_status()
        lines = [
            "📚 当前单词本状态\n",
            f"总词汇量: {result['total']}",
            f"学习中: {result['learning']}",
            f"已淘汰: {result['eliminated']}\n",
            "最近录入:",
        ]
        for w in result.get("recent_words", []):
            lines.append(f"• {w['word']} ({w['tags']}) - {w['added_at']}")
        return [TextContent(type="text", text="\n".join(lines))]

    elif name == "refresh_content":
        articles = await svc["content"].fetch_articles(force=True)
        if not articles:
            return [TextContent(type="text", text="⚠️ 内容刷新失败，请稍后再试。")]
        return [TextContent(type="text", text=f"✅ 内容已刷新，获取到 {len(articles)} 篇文章。")]

    return [TextContent(type="text", text=f"未知工具: {name}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
