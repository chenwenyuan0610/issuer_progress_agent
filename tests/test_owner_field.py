import unittest

from app.models import IssuerCreateRequest, ProgressUpdateRequest
from app.notion_client import NotionClient


class FakeNotionClient(NotionClient):
    def __init__(self):
        super().__init__()
        self.requests = []

    async def _tracker_data_source_id(self) -> str:
        return "tracker-data-source-id"

    async def _history_data_source_id(self) -> str:
        return "history-data-source-id"

    async def _request(self, method, path, json=None):
        self.requests.append({"method": method, "path": path, "json": json})
        if method == "POST" and path.endswith("/query"):
            return {"results": [self._page(owner="Diego")]}
        if method == "POST" and path == "/pages":
            owner_prop = json["properties"].get("Owner", {})
            owner = owner_prop.get("rich_text", [{}])[0].get("text", {}).get("content")
            return self._page(owner=owner)
        if method == "PATCH":
            return {"id": "issuer-page-id"}
        return {}

    @staticmethod
    def _page(owner=None):
        return {
            "id": "issuer-page-id",
            "properties": {
                "Issuer Name": {"title": [{"plain_text": "Kpay"}]},
                "Issuer OID": {"rich_text": []},
                "Region": {"select": None},
                "Service Type": {"select": None},
                "Current Stage": {"select": {"name": "Discovery"}},
                "Progress Status": {"status": {"name": "In progress"}},
                "Latest Progress": {"rich_text": []},
                "Next Action": {"rich_text": []},
                "Blocker": {"rich_text": []},
                "Owner": {"rich_text": [{"plain_text": owner or ""}]},
                "Last Update": {"last_edited_time": "2026-06-08T00:00:00.000Z"},
                "Go-Live Date": {"date": None},
            },
        }


class OwnerFieldTest(unittest.IsolatedAsyncioTestCase):
    async def test_create_issuer_writes_owner(self):
        client = FakeNotionClient()

        await client.create_issuer(IssuerCreateRequest(issuer_name="Kpay", owner="Diego"))

        create_payload = next(req["json"] for req in client.requests if req["method"] == "POST" and req["path"] == "/pages")
        self.assertEqual(
            create_payload["properties"]["Owner"],
            {"rich_text": [{"text": {"content": "Diego"}}]},
        )

    async def test_update_progress_writes_owner_when_provided(self):
        client = FakeNotionClient()

        await client.update_issuer_progress(
            "Kpay",
            ProgressUpdateRequest(latest_progress="Updated", owner="Alice"),
        )

        patch_payload = next(req["json"] for req in client.requests if req["method"] == "PATCH")
        self.assertEqual(
            patch_payload["properties"]["Owner"],
            {"rich_text": [{"text": {"content": "Alice"}}]},
        )


if __name__ == "__main__":
    unittest.main()
