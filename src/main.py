from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from loguru import logger

from src.adapters.command_router import CommandRouter
from src.adapters.feishu.bot import FeishuBot
from src.adapters.feishu.router import router as feishu_router
from src.config.settings import settings
from src.core.content import ContentService
from src.core.llm import LLMService
from src.core.reading import ReadingService
from src.core.review import ReviewService
from src.core.sentence import SentenceService
from src.core.stats import StatsService
from src.core.wordbook import WordbookService
from src.scheduler.jobs import SchedulerService
from src.storage.bitable import BitableStore
from src.storage.config_store import ConfigStore
from src.storage.reading_store import ReadingStore
from src.storage.wordbook_store import WordbookStore


def _init_services() -> dict:
    bitable = BitableStore()
    wordbook_store = WordbookStore(bitable)
    reading_store = ReadingStore(bitable)
    config_store = ConfigStore(bitable)

    llm = LLMService()
    wordbook = WordbookService(wordbook_store, llm)
    review = ReviewService(wordbook_store, llm)
    content = ContentService()
    reading = ReadingService(content, reading_store, wordbook_store, llm)
    sentence = SentenceService(llm)
    stats = StatsService(wordbook_store, reading_store, llm)

    command_router = CommandRouter(
        wordbook=wordbook,
        review=review,
        reading=reading,
        sentence=sentence,
        stats=stats,
        llm=llm,
        content=content,
    )

    return {
        "bitable": bitable,
        "wordbook_store": wordbook_store,
        "reading_store": reading_store,
        "config_store": config_store,
        "llm": llm,
        "wordbook": wordbook,
        "review": review,
        "content": content,
        "reading": reading,
        "sentence": sentence,
        "stats": stats,
        "command_router": command_router,
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    services = _init_services()
    command_router = services["command_router"]

    feishu_bot = FeishuBot(command_router)
    app.state.feishu_bot = feishu_bot
    app.state.services = services

    scheduler = SchedulerService(
        reading=services["reading"],
        stats=services["stats"],
        feishu_bot=feishu_bot,
    )
    scheduler.start()
    app.state.scheduler = scheduler

    logger.info("English Reading Agent started")

    yield

    scheduler.shutdown()
    logger.info("English Reading Agent stopped")


app = FastAPI(
    title="English Reading Agent",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(feishu_router)


@app.post("/trae/command")
async def trae_command(request: Request):
    body = await request.json()
    user_id = body.get("user_id", "trae_user")
    command = body.get("command", "")
    args = body.get("args", "")

    full_message = f"/{command} {args}".strip() if command else args

    command_router: CommandRouter = request.app.state.services["command_router"]
    try:
        reply = await command_router.handle(user_id, full_message)
        return {"code": 0, "data": {"reply": reply}}
    except Exception as e:
        logger.error("trae_command failed: {}", e)
        return {"code": -1, "msg": str(e)}


@app.post("/trae/chat")
async def trae_chat(request: Request):
    body = await request.json()
    user_id = body.get("user_id", "trae_user")
    message = body.get("message", "")

    if not message:
        return {"code": -1, "msg": "empty message"}

    command_router: CommandRouter = request.app.state.services["command_router"]
    try:
        reply = await command_router.handle(user_id, message)
        return {"code": 0, "data": {"reply": reply}}
    except Exception as e:
        logger.error("trae_chat failed: {}", e)
        return {"code": -1, "msg": str(e)}


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
