from __future__ import annotations

from fastapi import APIRouter, Request
from loguru import logger

from src.adapters.command_router import CommandRouter

router = APIRouter(prefix="/trae", tags=["trae"])


def create_trae_router(command_router: CommandRouter) -> APIRouter:
    @router.post("/command")
    async def handle_command(request: Request):
        body = await request.json()
        user_id = body.get("user_id", "trae_user")
        command = body.get("command", "")
        args = body.get("args", "")

        full_message = f"/{command} {args}".strip() if command else args

        try:
            reply = await command_router.handle(user_id, full_message)
            return {"code": 0, "data": {"reply": reply}}
        except Exception as e:
            logger.error("trae handle_command failed: {}", e)
            return {"code": -1, "msg": str(e)}

    @router.post("/chat")
    async def handle_chat(request: Request):
        body = await request.json()
        user_id = body.get("user_id", "trae_user")
        message = body.get("message", "")

        if not message:
            return {"code": -1, "msg": "empty message"}

        try:
            reply = await command_router.handle(user_id, message)
            return {"code": 0, "data": {"reply": reply}}
        except Exception as e:
            logger.error("trae handle_chat failed: {}", e)
            return {"code": -1, "msg": str(e)}

    return router
