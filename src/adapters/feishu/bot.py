from __future__ import annotations

from typing import Any

import lark_oapi as lark
from lark_oapi.api.im.v1 import (
    CreateMessageRequest,
    CreateMessageRequestBody,
)
from loguru import logger

from src.adapters.command_router import CommandRouter
from src.config.settings import settings


class FeishuBot:
    def __init__(self, router: CommandRouter) -> None:
        self._router = router
        self._client = lark.Client.builder() \
            .app_id(settings.feishu_app_id) \
            .app_secret(settings.feishu_app_secret) \
            .log_level(lark.LogLevel.DEBUG) \
            .build()

    async def handle_event(self, event_data: dict[str, Any]) -> None:
        try:
            header = event_data.get("header", {})
            event_type = header.get("event_type", "")

            if event_type != "im.message.receive_v1":
                return

            event = event_data.get("event", {})
            message = event.get("message", {})
            sender = event.get("sender", {})

            chat_id = message.get("chat_id", "")
            chat_type = message.get("chat_type", "")
            msg_type = message.get("message_type", "")
            content = message.get("content", "{}")

            user_id = sender.get("sender_id", {}).get("open_id", "")

            if msg_type != "text":
                return

            import json
            try:
                content_dict = json.loads(content)
                text = content_dict.get("text", "").strip()
            except json.JSONDecodeError:
                return

            if chat_type == "group":
                mention = event.get("message", {}).get("mentions", [])
                if not mention:
                    return
                for m in mention:
                    if m.get("name") == settings.feishu_app_id:
                        text = text.replace(f"@{m.get('key', '')}", "").strip()
                        break

            if not text:
                return

            reply = await self._router.handle(user_id, text)
            await self._send_message(chat_id, reply)

        except Exception as e:
            logger.error("handle_event failed: {}", e)

    async def _send_message(self, chat_id: str, text: str) -> None:
        try:
            import json
            content = json.dumps({"text": text})

            req = CreateMessageRequest.builder() \
                .receive_id_type("chat_id") \
                .request_body(
                    CreateMessageRequestBody.builder()
                    .receive_id(chat_id)
                    .msg_type("text")
                    .content(content)
                    .build()
                ) \
                .build()

            resp = self._client.im.v1.message.create(req)
            if not resp.success():
                logger.error("send_message failed: code={}, msg={}", resp.code, resp.msg)
        except Exception as e:
            logger.error("send_message exception: {}", e)

    async def send_to_user(self, open_id: str, text: str) -> None:
        try:
            import json
            content = json.dumps({"text": text})

            req = CreateMessageRequest.builder() \
                .receive_id_type("open_id") \
                .request_body(
                    CreateMessageRequestBody.builder()
                    .receive_id(open_id)
                    .msg_type("text")
                    .content(content)
                    .build()
                ) \
                .build()

            resp = self._client.im.v1.message.create(req)
            if not resp.success():
                logger.error("send_to_user failed: code={}, msg={}", resp.code, resp.msg)
        except Exception as e:
            logger.error("send_to_user exception: {}", e)
