from fastapi import FastAPI, Header, HTTPException, Depends
from .config import settings
from .models import IssuerCreateRequest, ProgressUpdateRequest, NoteCreateRequest
from .notion_client import NotionClient, NotionError

app = FastAPI(
    title="Issuer Progress AI Tool API",
    description="Tool API for an AI Agent that manages issuer onboarding progress in Notion.",
    version="0.1.0",
)


def require_api_key(
    x_api_key: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
) -> None:
    if not settings.api_key:
        return

    bearer_prefix = "Bearer "
    bearer_token = authorization[len(bearer_prefix) :] if authorization and authorization.startswith(bearer_prefix) else None

    if x_api_key != settings.api_key and bearer_token != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")


def notion() -> NotionClient:
    return NotionClient()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/issuers", dependencies=[Depends(require_api_key)])
async def create_issuer(req: IssuerCreateRequest, client: NotionClient = Depends(notion)):
    try:
        existing = await client.find_issuer(req.issuer_name)
        if existing:
            raise HTTPException(status_code=409, detail="Issuer already exists")
        return await client.create_issuer(req)
    except NotionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/issuers", dependencies=[Depends(require_api_key)])
async def list_issuers(stage: str | None = None, client: NotionClient = Depends(notion)):
    try:
        return await client.list_issuers(stage=stage)
    except NotionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/issuers/{issuer_name}", dependencies=[Depends(require_api_key)])
async def get_issuer(issuer_name: str, client: NotionClient = Depends(notion)):
    try:
        issuer = await client.find_issuer(issuer_name)
        if not issuer:
            raise HTTPException(status_code=404, detail="Issuer not found")
        return issuer
    except NotionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.patch("/issuers/{issuer_name}/progress", dependencies=[Depends(require_api_key)])
async def update_progress(issuer_name: str, req: ProgressUpdateRequest, client: NotionClient = Depends(notion)):
    try:
        return await client.update_issuer_progress(issuer_name, req)
    except NotionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/issuers/{issuer_name}/notes", dependencies=[Depends(require_api_key)])
async def add_note(issuer_name: str, req: NoteCreateRequest, client: NotionClient = Depends(notion)):
    try:
        page = await client.add_note(issuer_name, req)
        return {"status": "created", "page_id": page.get("id")}
    except NotionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/reports/weekly", dependencies=[Depends(require_api_key)])
async def weekly_report(client: NotionClient = Depends(notion)):
    try:
        issuers = await client.list_issuers()
    except NotionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    groups: dict[str, list[dict]] = {}
    for issuer in issuers:
        stage = issuer.current_stage or "Unknown"
        groups.setdefault(stage, []).append(issuer.model_dump())

    return {
        "title": "Issuer Weekly Progress Report",
        "total_issuers": len(issuers),
        "groups": groups,
        "summary_hint": "Let the AI Agent summarize groups by stage, next action, and blockers.",
    }
