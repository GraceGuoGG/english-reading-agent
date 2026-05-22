from __future__ import annotations

from typing import Any


def format_word_entry(data: dict[str, Any]) -> str:
    lines = [
        f"📖 新词录入: {data['word']}\n",
        f"【AI/技术场景释义】\n{data['definition']}\n",
        f"【典型例句】\n{data['example']}",
    ]
    if data.get("example_source"):
        lines.append(f"— {data['example_source']}")
    if data.get("tags"):
        lines.append(f"\n【标签】{' | '.join(data['tags'])}")
    lines.append(f"\n【难度】{data.get('difficulty', '中级')}")
    return "\n".join(lines)


def format_reading_article(article: dict[str, Any]) -> str:
    lines = [
        f"📖 {article['title']}\n",
        f"来源: {article['source']} | 字数: {article['word_count']} | 难度: {article['difficulty']}",
        f"链接: {article['url']}\n",
        article["content"],
    ]
    return "\n".join(lines)


def format_quiz(words: list[dict[str, Any]]) -> str:
    lines = [f"📝 专业词汇复习 (1/{len(words)})\n"]
    for i, w in enumerate(words, 1):
        lines.append(f"{i}. {w['word']}: ____________")
    lines.append("\n请回复你的答案，格式：1.xxx 2.xxx ...")
    return "\n".join(lines)


def format_quiz_result(result: dict[str, Any]) -> str:
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

    return "\n".join(lines)


def format_wordbook_stats(stats: dict[str, Any]) -> str:
    lines = [
        "📚 当前单词本状态\n",
        f"总词汇量: {stats['total']}",
        f"学习中: {stats['learning']}",
        f"已淘汰: {stats['eliminated']}\n",
        "最近录入:",
    ]
    for w in stats.get("recent_words", []):
        lines.append(f"• {w['word']} ({w['tags']}) - {w['added_at']}")
    return "\n".join(lines)


def format_sentence_parse(result: dict[str, Any]) -> str:
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
    return "\n".join(lines)
