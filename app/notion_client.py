from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import httpx
from .config import settings
from .models import IssuerProgress, IssuerCreateRequest, ProgressUpdateRequest, NoteCreateRequest


class NotionError(RuntimeError):
    pass


class NotionClient:
    def __init__(self) -> None:
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {settings.notion_token}",
            "Notion-Version": settings.notion_version,
            "Content-Type": "application/json",
        }
        self._data_source_cache: dict[str, str] = {}

    async def _request(self, method: str, path: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.request(method, f"{self.base_url}{path}", headers=self.headers, json=json)
        if resp.status_code >= 400:
            raise NotionError(f"Notion API error {resp.status_code}: {resp.text}")
        return resp.json()

    async def _resolve_data_source_id(self, label: str, database_id: str | None, configured_id: str | None) -> str:
        if configured_id:
            return configured_id
        if not database_id:
            raise NotionError(f"{label} data source is not configured")
        if database_id in self._data_source_cache:
            return self._data_source_cache[database_id]

        data = await self._request("GET", f"/databases/{database_id}")
        data_sources = data.get("data_sources") or []
        if not data_sources:
            raise NotionError(f"No data sources found for {label} database: {database_id}")

        data_source_id = data_sources[0].get("id")
        if not data_source_id:
            raise NotionError(f"Could not resolve {label} data source id from database: {database_id}")

        self._data_source_cache[database_id] = data_source_id
        return data_source_id

    async def _tracker_data_source_id(self) -> str:
        return await self._resolve_data_source_id(
            "issuer tracker",
            settings.issuer_tracker_db_id,
            settings.issuer_tracker_data_source_id,
        )

    async def _history_data_source_id(self) -> str:
        return await self._resolve_data_source_id(
            "issuer history",
            settings.issuer_history_db_id,
            settings.issuer_history_data_source_id,
        )

    async def _notes_data_source_id(self) -> str:
        return await self._resolve_data_source_id(
            "issuer notes",
            settings.issuer_notes_db_id,
            settings.issuer_notes_data_source_id,
        )

    @staticmethod
    def _title(value: str) -> dict[str, Any]:
        return {"title": [{"text": {"content": value}}]}

    @staticmethod
    def _rich_text(value: str | None) -> dict[str, Any]:
        return {"rich_text": [{"text": {"content": value or ""}}]}

    @staticmethod
    def _select(value: str | None) -> dict[str, Any]:
        return {"select": {"name": value}} if value else {"select": None}

    @staticmethod
    def _status(value: str | None) -> dict[str, Any]:
        return {"status": {"name": value}} if value else {"status": None}

    @staticmethod
    def _multi_select(values: list[str] | None) -> dict[str, Any]:
        return {"multi_select": [{"name": v} for v in (values or [])]}

    @staticmethod
    def _service_type(values: list[str] | None) -> dict[str, Any]:
        value = values[0] if values else None
        return {"select": {"name": value}} if value else {"select": None}

    @staticmethod
    def _date(value: str | None) -> dict[str, Any]:
        return {"date": {"start": value}} if value else {"date": None}

    @staticmethod
    def _get_title(props: dict[str, Any], name: str) -> str | None:
        items = props.get(name, {}).get("title", [])
        return "".join(item.get("plain_text", "") for item in items) or None

    @staticmethod
    def _get_text(props: dict[str, Any], name: str) -> str | None:
        items = props.get(name, {}).get("rich_text", [])
        return "".join(item.get("plain_text", "") for item in items) or None

    @staticmethod
    def _get_select(props: dict[str, Any], name: str) -> str | None:
        value = props.get(name, {}).get("select")
        return value.get("name") if value else None

    @staticmethod
    def _get_status(props: dict[str, Any], name: str) -> str | None:
        value = props.get(name, {}).get("status")
        return value.get("name") if value else None

    @staticmethod
    def _get_multi_select(props: dict[str, Any], name: str) -> list[str]:
        return [v.get("name") for v in props.get(name, {}).get("multi_select", []) if v.get("name")]

    def _get_service_type(self, props: dict[str, Any], name: str) -> list[str]:
        multi_select = self._get_multi_select(props, name)
        if multi_select:
            return multi_select
        select = self._get_select(props, name)
        return [select] if select else []

    @staticmethod
    def _get_date(props: dict[str, Any], name: str) -> str | None:
        value = props.get(name, {}).get("date")
        return value.get("start") if value else None

    def _get_date_or_last_edited_time(self, props: dict[str, Any], name: str) -> str | None:
        return self._get_date(props, name) or props.get(name, {}).get("last_edited_time")

    @staticmethod
    def _get_people(props: dict[str, Any], name: str) -> str | None:
        people = props.get(name, {}).get("people", [])
        names = [person.get("name") for person in people if person.get("name")]
        return ", ".join(names) or None

    def _parse_issuer(self, page: dict[str, Any]) -> IssuerProgress:
        props = page["properties"]
        return IssuerProgress(
            page_id=page["id"],
            issuer_name=self._get_title(props, "Issuer Name") or "",
            issuer_oid=self._get_text(props, "Issuer OID"),
            region=self._get_select(props, "Region"),
            service_type=self._get_service_type(props, "Service Type"),
            current_stage=self._get_select(props, "Current Stage"),
            progress_status=self._get_status(props, "Progress Status") or self._get_select(props, "Progress Status"),
            latest_progress=self._get_text(props, "Latest Progress"),
            next_action=self._get_text(props, "Next Action"),
            risk_level=self._get_select(props, "Risk Level"),
            blocker=self._get_text(props, "Blocker"),
            owner=self._get_people(props, "Owner") or self._get_text(props, "Owner"),
            last_update=self._get_date_or_last_edited_time(props, "Last Update"),
            go_live_date=self._get_date(props, "Go-Live Date"),
        )

    async def find_issuer(self, issuer_name: str) -> IssuerProgress | None:
        data_source_id = await self._tracker_data_source_id()
        payload = {
            "filter": {
                "property": "Issuer Name",
                "title": {"equals": issuer_name},
            },
            "page_size": 1,
        }
        data = await self._request("POST", f"/data_sources/{data_source_id}/query", payload)
        results = data.get("results", [])
        if not results:
            return None
        return self._parse_issuer(results[0])

    async def list_issuers(self, stage: str | None = None, risk_level: str | None = None) -> list[IssuerProgress]:
        data_source_id = await self._tracker_data_source_id()
        filters = []
        if stage:
            filters.append({"property": "Current Stage", "select": {"equals": stage}})
        if risk_level:
            filters.append({"property": "Risk Level", "select": {"equals": risk_level}})
        payload: dict[str, Any] = {"page_size": 100}
        if len(filters) == 1:
            payload["filter"] = filters[0]
        elif len(filters) > 1:
            payload["filter"] = {"and": filters}
        data = await self._request("POST", f"/data_sources/{data_source_id}/query", payload)
        return [self._parse_issuer(page) for page in data.get("results", [])]

    async def create_issuer(self, req: IssuerCreateRequest) -> IssuerProgress:
        data_source_id = await self._tracker_data_source_id()
        props = {
            "Issuer Name": self._title(req.issuer_name),
            "Issuer OID": self._rich_text(req.issuer_oid),
            "Region": self._select(req.region),
            "Service Type": self._service_type(req.service_type),
            "Current Stage": self._select(req.current_stage),
            "Progress Status": self._status(req.progress_status),
            "Latest Progress": self._rich_text(req.latest_progress),
            "Next Action": self._rich_text(req.next_action),
            "Risk Level": self._select(req.risk_level),
            "Go-Live Date": self._date(req.go_live_date.isoformat() if req.go_live_date else None),
        }
        payload = {
            "parent": {"type": "data_source_id", "data_source_id": data_source_id},
            "properties": props,
        }
        page = await self._request("POST", "/pages", payload)
        return self._parse_issuer(page)

    async def update_issuer_progress(self, issuer_name: str, req: ProgressUpdateRequest) -> IssuerProgress:
        issuer = await self.find_issuer(issuer_name)
        if not issuer:
            raise NotionError(f"Issuer not found: {issuer_name}")
        old_stage = issuer.current_stage
        new_stage = req.current_stage or issuer.current_stage
        props: dict[str, Any] = {
            "Latest Progress": self._rich_text(req.latest_progress),
        }
        if req.current_stage:
            props["Current Stage"] = self._select(req.current_stage)
        if req.progress_status:
            props["Progress Status"] = self._status(req.progress_status)
        if req.next_action is not None:
            props["Next Action"] = self._rich_text(req.next_action)
        if req.risk_level:
            props["Risk Level"] = self._select(req.risk_level)
        if req.blocker is not None:
            props["Blocker"] = self._rich_text(req.blocker)

        await self._request("PATCH", f"/pages/{issuer.page_id}", {"properties": props})
        await self.add_history(
            issuer_page_id=issuer.page_id,
            issuer_name=issuer.issuer_name,
            old_stage=old_stage,
            new_stage=new_stage,
            change_note=req.latest_progress,
            next_action=req.next_action,
            risk_level=req.risk_level or issuer.risk_level,
            updated_by=req.updated_by,
        )
        updated = await self.find_issuer(issuer_name)
        if not updated:
            raise NotionError("Issuer disappeared after update")
        return updated

    async def add_history(
        self,
        issuer_page_id: str,
        issuer_name: str,
        old_stage: str | None,
        new_stage: str | None,
        change_note: str,
        next_action: str | None,
        risk_level: str | None,
        updated_by: str,
    ) -> dict[str, Any]:
        data_source_id = await self._history_data_source_id()
        today = datetime.now(timezone.utc).date().isoformat()
        props = {
            "Name": self._title(f"{issuer_name} - {today}"),
            "Issuer": {"relation": [{"id": issuer_page_id}]},
            "Change Date": self._date(today),
            "Old Stage": self._select(old_stage),
            "New Stage": self._select(new_stage),
            "Change Note": self._rich_text(change_note),
            "Next Action": self._rich_text(next_action),
            "Risk Level": self._select(risk_level),
            "Updated By": self._rich_text(updated_by),
        }
        return await self._request(
            "POST",
            "/pages",
            {"parent": {"type": "data_source_id", "data_source_id": data_source_id}, "properties": props},
        )

    async def add_note(self, issuer_name: str, req: NoteCreateRequest) -> dict[str, Any]:
        if not settings.issuer_notes_db_id and not settings.issuer_notes_data_source_id:
            raise NotionError("ISSUER_NOTES_DB_ID is not configured")
        data_source_id = await self._notes_data_source_id()
        issuer = await self.find_issuer(issuer_name)
        if not issuer:
            raise NotionError(f"Issuer not found: {issuer_name}")
        source_date = req.source_date.isoformat() if req.source_date else datetime.now(timezone.utc).date().isoformat()
        props = {
            "Title": self._title(req.title),
            "Issuer": {"relation": [{"id": issuer.page_id}]},
            "Note Type": self._select(req.note_type),
            "Content": self._rich_text(req.content[:1900]),
            "Source Date": self._date(source_date),
            "Created By": self._rich_text(req.created_by),
        }
        return await self._request(
            "POST",
            "/pages",
            {"parent": {"type": "data_source_id", "data_source_id": data_source_id}, "properties": props},
        )
