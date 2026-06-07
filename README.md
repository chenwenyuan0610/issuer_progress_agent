# Issuer Progress AI Agent MVP

這是一個「發卡行進度管理 AI Agent」MVP。

- Notion Database：當進度記憶庫
- FastAPI：當 AI Tool API
- AI Agent：透過 OpenAPI / Actions / MCP / CLI 呼叫這些 API

## 功能

1. 新增發卡行
2. 查詢發卡行目前進度
3. 更新發卡行進度
4. 自動寫入進度歷史紀錄
5. 依 stage / risk 查詢
6. 產生週報原始資料
7. 新增會議 / Email / Issue note

## Notion 設定

1. 建立 Notion internal integration，取得 token。
2. 建立 2~3 張 database：
   - Issuer Progress Tracker
   - Issuer Progress History
   - Issuer Notes，可選
3. 把這些 database 分享給 integration。
4. 複製 database id，填入 `.env`。

欄位請參考 `docs/notion_schema.md`。

## 本機啟動

```bash
cp .env.example .env
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
```

測試：

```bash
curl http://localhost:8080/health
```

## API Key

所有業務 API 都需要 header：

```bash
x-api-key: change-me
```


## 建立 issuer

```bash
curl -X POST http://localhost:8080/issuers \
  -H 'Content-Type: application/json' \
  -H 'x-api-key: change-me' \
  -d '{
    "issuer_name": "Kpay",
    "region": "TH",
    "service_type": ["ACS"],
    "current_stage": "UI Confirming",
    "progress_status": "In Progress",
    "latest_progress": "接口問題已解決，目前等待客戶確認 UI",
    "next_action": "等待客戶回覆 UI 確認結果",
    "risk_level": "Medium",
    "owner": "Diego"
  }'
```

## 查詢 issuer

```bash
curl http://localhost:8080/issuers/Kpay \
  -H 'x-api-key: change-me'
```

## 更新 issuer 進度

```bash
curl -X PATCH http://localhost:8080/issuers/Kpay/progress \
  -H 'Content-Type: application/json' \
  -H 'x-api-key: change-me' \
  -d '{
    "current_stage": "SIT",
    "progress_status": "In Progress",
    "latest_progress": "UI 已確認，準備進 SIT",
    "next_action": "安排 SIT 測試與確認交易流程",
    "risk_level": "Low",
    "updated_by": "Diego"
  }'
```

## 列出 UAT issuer

```bash
curl 'http://localhost:8080/issuers?stage=UAT' \
  -H 'x-api-key: change-me'
```

## 週報資料

```bash
curl http://localhost:8080/reports/weekly \
  -H 'x-api-key: change-me'
```

## AI Agent Prompt

請使用 `app/agent_prompt.md` 當 AI Agent 的 system prompt。

## 接 ChatGPT Actions / GPTs

把 `openapi-actions.yaml` 裡面的 `servers.url` 改成你的 API 網址，然後匯入到 Actions。

## 部署建議

正式 PoC 建議：

```text
User / GPT / CLI
  -> issuer-progress-tool-api
  -> Notion API
  -> Notion Database
```

不要把 Notion token 放在前端、prompt 或 GPT 設定裡，應該放在後端 `.env` 或 Secret Manager。
