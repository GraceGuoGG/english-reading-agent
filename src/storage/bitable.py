from __future__ import annotations

from typing import Any

import lark_oapi as lark
from lark_oapi.api.bitable.v1 import (
    BatchCreateAppTableRecordRequest,
    BatchCreateAppTableRecordResponse,
    CreateAppTableRecordRequest,
    CreateAppTableRecordResponse,
    DeleteAppTableRecordRequest,
    DeleteAppTableRecordResponse,
    ListAppTableRecordRequest,
    ListAppTableRecordResponse,
    SearchAppTableRecordRequest,
    SearchAppTableRecordResponse,
    UpdateAppTableRecordRequest,
    UpdateAppTableRecordResponse,
)
from loguru import logger

from src.config.settings import settings


class BitableStore:
    def __init__(self) -> None:
        self.client = lark.Client.builder() \
            .app_id(settings.feishu_app_id) \
            .app_secret(settings.feishu_app_secret) \
            .build()
        self.app_token = settings.bitable_app_token

    async def list_records(
        self,
        table_id: str,
        filter_expr: str | None = None,
        sort: list[dict] | None = None,
        page_size: int = 100,
        page_token: str | None = None,
    ) -> list[dict[str, Any]]:
        all_records: list[dict[str, Any]] = []
        current_token = page_token

        while True:
            builder = ListAppTableRecordRequest.builder() \
                .app_token(self.app_token) \
                .table_id(table_id) \
                .page_size(page_size)

            if filter_expr:
                builder = builder.filter(filter_expr)
            if sort:
                sort_str = ",".join(f'{s["field_name"]} {s["desc"]}' for s in sort)
                builder = builder.sort(sort_str)
            if current_token:
                builder = builder.page_token(current_token)

            req = builder.build()
            resp: ListAppTableRecordResponse = self.client.bitable.v1.app_table_record.list(req)

            if not resp.success():
                logger.error("list_records failed: code={}, msg={}", resp.code, resp.msg)
                break

            if resp.data and resp.data.items:
                for item in resp.data.items:
                    all_records.append({"record_id": item.record_id, "fields": item.fields})

            if not resp.data or not resp.data.has_more:
                break
            current_token = resp.data.page_token

        return all_records

    async def create_record(self, table_id: str, fields: dict[str, Any]) -> str | None:
        req = CreateAppTableRecordRequest.builder() \
            .app_token(self.app_token) \
            .table_id(table_id) \
            .request_body(lark.bitable.AppTableRecord.builder().fields(fields).build()) \
            .build()

        resp: CreateAppTableRecordResponse = self.client.bitable.v1.app_table_record.create(req)

        if not resp.success():
            logger.error("create_record failed: code={}, msg={}", resp.code, resp.msg)
            return None

        return resp.data.record.record_id

    async def update_record(self, table_id: str, record_id: str, fields: dict[str, Any]) -> bool:
        req = UpdateAppTableRecordRequest.builder() \
            .app_token(self.app_token) \
            .table_id(table_id) \
            .record_id(record_id) \
            .request_body(lark.bitable.AppTableRecord.builder().fields(fields).record_id(record_id).build()) \
            .build()

        resp: UpdateAppTableRecordResponse = self.client.bitable.v1.app_table_record.update(req)

        if not resp.success():
            logger.error("update_record failed: code={}, msg={}", resp.code, resp.msg)
            return False

        return True

    async def delete_record(self, table_id: str, record_id: str) -> bool:
        req = DeleteAppTableRecordRequest.builder() \
            .app_token(self.app_token) \
            .table_id(table_id) \
            .record_id(record_id) \
            .build()

        resp: DeleteAppTableRecordResponse = self.client.bitable.v1.app_table_record.delete(req)

        if not resp.success():
            logger.error("delete_record failed: code={}, msg={}", resp.code, resp.msg)
            return False

        return True

    async def batch_create_records(self, table_id: str, records: list[dict[str, Any]]) -> list[str] | None:
        bodies = [
            lark.bitable.AppTableRecord.builder().fields(r).build()
            for r in records
        ]
        req = BatchCreateAppTableRecordRequest.builder() \
            .app_token(self.app_token) \
            .table_id(table_id) \
            .request_body(lark.bitable.BatchCreateAppTableRecordRequestBody.builder().records(bodies).build()) \
            .build()

        resp: BatchCreateAppTableRecordResponse = self.client.bitable.v1.app_table_record.batch_create(req)

        if not resp.success():
            logger.error("batch_create_records failed: code={}, msg={}", resp.code, resp.msg)
            return None

        return [r.record_id for r in resp.data.records]

    async def search_records(
        self,
        table_id: str,
        condition: dict[str, Any] | None = None,
        page_size: int = 100,
    ) -> list[dict[str, Any]]:
        con = condition or {}
        req = SearchAppTableRecordRequest.builder() \
            .app_token(self.app_token) \
            .table_id(table_id) \
            .request_body(
                lark.bitable.SearchAppTableRecordRequestBody.builder()
                .page_size(page_size)
                .condition(lark.bitable.AppTableRecordCondition.builder()
                           .conjunction("and")
                           .build() if not con else
                           lark.bitable.AppTableRecordCondition.builder()
                           .conjunction("and")
                           .build())
                .build()
            ) \
            .build()

        resp: SearchAppTableRecordResponse = self.client.bitable.v1.app_table_record.search(req)

        if not resp.success():
            logger.error("search_records failed: code={}, msg={}", resp.code, resp.msg)
            return []

        results: list[dict[str, Any]] = []
        if resp.data and resp.data.items:
            for item in resp.data.items:
                results.append({"record_id": item.record_id, "fields": item.fields})

        return results
