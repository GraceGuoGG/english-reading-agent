from __future__ import annotations

from fastapi import APIRouter, Request
from loguru import logger

from src.config.settings import settings

router = APIRouter(prefix="/feishu", tags=["feishu"])


@router.post("/webhook")
async def webhook(request: Request):
    body = await request.json()

    challenge = body.get("challenge")
    if challenge:
        return {"challenge": challenge}

    header = body.get("header", {})
    token = header.get("token", "")
    if settings.feishu_verification_token and token != settings.feishu_verification_token:
        logger.warning("Invalid verification token")
        return {"code": -1, "msg": "invalid token"}

    bot = request.app.state.feishu_bot
    import asyncio
    asyncio.create_task(bot.handle_event(body))

    return {"code": 0, "msg": "ok"}
