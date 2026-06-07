from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import httpx


OPENAI_URL = "https://api.openai.com/v1/responses"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def env(name: str, default: str | None = None) -> str | None:
    return os.environ.get(name) or read_env_file(repo_root() / ".env").get(name) or default


def api_base() -> str:
    return env("ISSUER_AGENT_API_BASE", "http://127.0.0.1:8080").rstrip("/")


def api_key() -> str:
    return env("API_KEY", "change-me")


def call_tool(name: str, args: dict[str, Any]) -> Any:
    headers = {"x-api-key": api_key()}
    base = api_base()

    with httpx.Client(timeout=30.0) as client:
        if name == "listIssuers":
            params = {k: v for k, v in args.items() if v is not None}
            return client.get(f"{base}/issuers", headers=headers, params=params).json()

        if name == "getIssuerProgress":
            issuer_name = args["issuer_name"]
            return client.get(f"{base}/issuers/{issuer_name}", headers=headers).json()

        if name == "generateWeeklyReport":
            return client.get(f"{base}/reports/weekly", headers=headers).json()

        if name == "createIssuer":
            return client.post(f"{base}/issuers", headers=headers, json=args).json()

        if name == "updateIssuerProgress":
            issuer_name = args.pop("issuer_name")
            return client.patch(f"{base}/issuers/{issuer_name}/progress", headers=headers, json=args).json()

    raise ValueError(f"Unknown tool: {name}")


TOOLS = [
    {
        "type": "function",
        "name": "listIssuers",
        "description": "List issuer progress records, optionally filtered by stage or risk level.",
        "parameters": {
            "type": "object",
            "properties": {
                "stage": {
                    "type": "string",
                    "enum": ["Discovery", "Planning", "Implementation", "Testing", "Go-Live", "Post Go-Live"],
                },
                "risk_level": {"type": "string", "enum": ["Low", "Medium", "High"]},
            },
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "getIssuerProgress",
        "description": "Get one issuer progress record by issuer name.",
        "parameters": {
            "type": "object",
            "properties": {"issuer_name": {"type": "string"}},
            "required": ["issuer_name"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "generateWeeklyReport",
        "description": "Get raw weekly report data for AI summarization.",
        "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "type": "function",
        "name": "createIssuer",
        "description": "Create a new issuer progress record.",
        "parameters": {
            "type": "object",
            "properties": {
                "issuer_name": {"type": "string"},
                "issuer_oid": {"type": "string"},
                "region": {"type": "string"},
                "service_type": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["Onboarding", "Migration", "Support", "Other"]},
                },
                "current_stage": {
                    "type": "string",
                    "enum": ["Discovery", "Planning", "Implementation", "Testing", "Go-Live", "Post Go-Live"],
                },
                "progress_status": {"type": "string", "enum": ["Not started", "In progress", "Blocked", "Done"]},
                "latest_progress": {"type": "string"},
                "next_action": {"type": "string"},
                "risk_level": {"type": "string", "enum": ["Low", "Medium", "High"]},
                "go_live_date": {"type": "string", "description": "ISO date, e.g. 2026-07-01"},
            },
            "required": ["issuer_name"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "updateIssuerProgress",
        "description": "Update issuer progress and append history.",
        "parameters": {
            "type": "object",
            "properties": {
                "issuer_name": {"type": "string"},
                "current_stage": {
                    "type": "string",
                    "enum": ["Discovery", "Planning", "Implementation", "Testing", "Go-Live", "Post Go-Live"],
                },
                "progress_status": {"type": "string", "enum": ["Not started", "In progress", "Blocked", "Done"]},
                "latest_progress": {"type": "string"},
                "next_action": {"type": "string"},
                "risk_level": {"type": "string", "enum": ["Low", "Medium", "High"]},
                "blocker": {"type": "string"},
                "updated_by": {"type": "string"},
            },
            "required": ["issuer_name", "latest_progress"],
            "additionalProperties": False,
        },
    },
]


def create_response(openai_key: str, payload: dict[str, Any]) -> dict[str, Any]:
    headers = {"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"}
    with httpx.Client(timeout=90.0) as client:
        response = client.post(OPENAI_URL, headers=headers, json=payload)
        if response.status_code >= 400:
            raise RuntimeError(f"OpenAI API error {response.status_code}: {response.text}")
        return response.json()


def output_text(response: dict[str, Any]) -> str:
    if response.get("output_text"):
        return response["output_text"]
    chunks: list[str] = []
    for item in response.get("output", []):
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"}:
                chunks.append(content.get("text", ""))
    return "".join(chunks)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a local AI agent test against the issuer progress API.")
    parser.add_argument(
        "message",
        nargs="?",
        default="請查詢目前所有 issuer，整理一份簡短週報摘要。",
        help="User message to send to the agent.",
    )
    parser.add_argument("--model", default=env("OPENAI_MODEL", "gpt-5-mini"))
    args = parser.parse_args()

    openai_key = env("OPENAI_API_KEY")
    if not openai_key:
        print("OPENAI_API_KEY is missing. Set it in your shell or .env, then run again.", file=sys.stderr)
        return 2

    prompt = (repo_root() / "app" / "agent_prompt.md").read_text(encoding="utf-8")
    input_items: list[dict[str, Any]] = [{"role": "user", "content": args.message}]

    for step in range(6):
        response = create_response(
            openai_key,
            {
                "model": args.model,
                "instructions": prompt,
                "input": input_items,
                "tools": TOOLS,
                "parallel_tool_calls": False,
            },
        )
        input_items.extend(response.get("output", []))

        function_calls = [item for item in response.get("output", []) if item.get("type") == "function_call"]
        if not function_calls:
            print(output_text(response))
            return 0

        for call in function_calls:
            tool_name = call["name"]
            tool_args = json.loads(call.get("arguments") or "{}")
            print(f"[tool] {tool_name}({json.dumps(tool_args, ensure_ascii=False)})")
            tool_result = call_tool(tool_name, dict(tool_args))
            print(f"[tool-result] {json.dumps(tool_result, ensure_ascii=False)[:1000]}")
            input_items.append(
                {
                    "type": "function_call_output",
                    "call_id": call["call_id"],
                    "output": json.dumps(tool_result, ensure_ascii=False),
                }
            )

    print("Stopped after too many tool-calling steps.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
