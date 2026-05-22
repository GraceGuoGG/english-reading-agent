from __future__ import annotations

from typing import Any

from src.core.content import ContentService
from src.core.llm import LLMService
from src.core.reading import ReadingService
from src.core.review import ReviewService
from src.core.sentence import SentenceService
from src.core.stats import StatsService
from src.core.wordbook import WordbookService

HELP_TEXT = """📖 AI 技术英文阅读陪练 - 命令列表

📚 学习命令：
/english 或 开始学习 - 开始今日阅读训练
/review 或 复习单词 - 启动单词复习考核
/wordbook 或 查看单词本 - 查看单词本状态
/stats 或 学习统计 - 查看学习进度统计

📖 查词命令：
[单词] - 查询单词释义，如 integration
[单词]是什么意思 - 查询释义，如 orchestration是什么意思
拆解[句子] - 长难句拆解

⚙️ 管理命令：
/refresh 或 刷新推送 - 手动触发内容推送
/export 或 导出单词本 - 导出单词本
/settings 或 设置 - 查看/修改设置
/help 或 帮助 - 查看帮助信息"""


class CommandRouter:
    def __init__(
        self,
        wordbook: WordbookService,
        review: ReviewService,
        reading: ReadingService,
        sentence: SentenceService,
        stats: StatsService,
        llm: LLMService,
        content: ContentService,
    ) -> None:
        self._wordbook = wordbook
        self._review = review
        self._reading = reading
        self._sentence = sentence
        self._stats = stats
        self._llm = llm
        self._content = content
        self._active_quiz: dict[str, list[dict[str, Any]]] = {}

    async def handle(self, user_id: str, message: str) -> str:
        intent_data = await self._llm.recognize_intent(message)
        intent = intent_data.get("intent", "chat")
        args = intent_data.get("args", "")

        handler = {
            "start_reading": self._handle_start_reading,
            "review": self._handle_review,
            "wordbook": self._handle_wordbook,
            "stats": self._handle_stats,
            "help": self._handle_help,
            "refresh": self._handle_refresh,
            "export": self._handle_export,
            "settings": self._handle_settings,
            "lookup": self._handle_lookup,
            "parse_sentence": self._handle_parse_sentence,
            "chat": self._handle_chat,
        }.get(intent, self._handle_chat)

        return await handler(user_id, args)

    async def _handle_start_reading(self, user_id: str, args: str) -> str:
        result = await self._reading.start_reading()
        if "error" in result:
            return result["error"]

        text = (
            f"📖 今日阅读训练\n\n"
            f"【{result['title']}】\n"
            f"来源: {result['source']} | 字数: {result['word_count']} | 难度: {result['difficulty']}\n"
            f"链接: {result['url']}\n\n"
            f"{result['content']}\n\n"
            f"---\n{result['instructions']}"
        )
        return text

    async def _handle_review(self, user_id: str, args: str) -> str:
        quiz = await self._review.generate_quiz()
        if not quiz["words"]:
            return quiz["message"]

        self._active_quiz[user_id] = quiz["words"]

        lines = [f"📝 专业词汇复习 (1/{quiz['total']})\n"]
        for i, w in enumerate(quiz["words"], 1):
            lines.append(f"{i}. {w['word']}: ____________")
        lines.append("\n请回复你的答案，格式：1.xxx 2.xxx ...")

        return "\n".join(lines)

    async def _handle_wordbook(self, user_id: str, args: str) -> str:
        stats = await self._wordbook.get_wordbook_status()

        lines = [
            "📚 当前单词本状态\n",
            f"总词汇量: {stats['total']}",
            f"学习中: {stats['learning']}",
            f"已淘汰: {stats['eliminated']}\n",
            "最近录入:",
        ]
        for w in stats.get("recent_words", []):
            lines.append(f"• {w['word']} ({w['tags']}) - {w['added_at']}")

        lines.append("\n[输入 /review 开始复习] [输入 /export 导出单词本]")
        return "\n".join(lines)

    async def _handle_stats(self, user_id: str, args: str) -> str:
        overview = await self._stats.get_stats_overview()

        return (
            f"📊 学习统计\n\n"
            f"今日阅读: {overview['today_readings']} 篇\n"
            f"本周阅读: {overview['weekly_readings']} 篇\n"
            f"本周平均阅读时长: {overview['weekly_avg_duration']} 分钟/篇\n\n"
            f"单词本总量: {overview['wordbook_total']}\n"
            f"学习中: {overview['wordbook_learning']}\n"
            f"已淘汰: {overview['wordbook_eliminated']}"
        )

    async def _handle_help(self, user_id: str, args: str) -> str:
        return HELP_TEXT

    async def _handle_refresh(self, user_id: str, args: str) -> str:
        articles = await self._content.fetch_articles(force=True)
        if not articles:
            return "⚠️ 内容刷新失败，请稍后再试。"
        return f"✅ 内容已刷新，获取到 {len(articles)} 篇文章。输入 /english 开始阅读。"

    async def _handle_export(self, user_id: str, args: str) -> str:
        words = await self._wordbook._store.list_words()
        if not words:
            return "单词本为空，暂无内容可导出。"

        lines = ["📖 单词本导出\n"]
        for w in words:
            f = w["fields"]
            status = f.get("status", "")
            lines.append(
                f"• {f.get('word', '')} | {f.get('definition', '')} | {status}"
            )

        return "\n".join(lines)

    async def _handle_settings(self, user_id: str, args: str) -> str:
        return "⚙️ 当前设置\n\n推送时间: 07:30\n每日短篇: 1\n每日中篇: 1\n难度偏好: 自适应\n\n如需修改，请联系管理员。"

    async def _handle_lookup(self, user_id: str, args: str) -> str:
        if not args:
            return "请输入要查询的单词。"

        result = await self._wordbook.lookup_word(args.strip())

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

        return "\n".join(lines)

    async def _handle_parse_sentence(self, user_id: str, args: str) -> str:
        if not args:
            return "请输入要拆解的句子。"

        result = await self._sentence.parse_sentence(args)

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

    async def _handle_chat(self, user_id: str, args: str) -> str:
        if not args:
            return "你好！输入 /help 查看可用命令。"

        quiz_words = self._active_quiz.get(user_id)
        if quiz_words:
            answers = self._parse_quiz_answers(args)
            if answers:
                result = await self._review.evaluate_answers(answers, quiz_words)
                del self._active_quiz[user_id]
                return self._format_quiz_result(result)

        return (
            "我专注于 AI/技术英文阅读训练，不处理其他话题。\n"
            "输入 /help 查看可用命令，或直接发送英文单词查询释义。"
        )

    def _parse_quiz_answers(self, text: str) -> dict[str, str]:
        answers: dict[str, str] = {}
        parts = text.strip().split()
        for part in parts:
            if "." in part:
                idx, _, ans = part.partition(".")
                if idx.isdigit():
                    answers[idx] = ans
        return answers if answers else {}

    def _format_quiz_result(self, result: dict[str, Any]) -> str:
        lines = []
        for r in result["results"]:
            if r["correct"]:
                lines.append(
                    f"✅ 第{r['index']}题正确\n"
                    f"   {r['word']}: {r['standard_definition']}"
                )
            else:
                lines.append(
                    f"❌ 第{r['index']}题错误\n"
                    f"   你的答案: {r['user_answer']}\n"
                    f"   标准答案: {r['standard_definition']}"
                )
                if r.get("example"):
                    lines.append(f"   例句: {r['example']}")

        lines.append(
            f"\n📊 正确率: {result['accuracy']}% "
            f"({result['correct_count']}/{result['total']})"
        )

        if result.get("eliminated_words"):
            lines.append(
                f"\n🎉 以下单词连续3次正确，已从单词本淘汰: "
                f"{', '.join(result['eliminated_words'])}"
            )

        return "\n".join(lines)
