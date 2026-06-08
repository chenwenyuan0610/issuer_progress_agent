# Notion Database Schema

建立 3 張 Notion Database，欄位名稱請盡量完全一致，因為程式會依照 property name 存取。

## 1. Issuer Progress Tracker

| Property | Type | Example |
|---|---|---|
| Issuer Name | Title | Kpay |
| Issuer OID | Text | 9 |
| Region | Select | TH |
| Service Type | Select | Onboarding |
| Current Stage | Select | UI Confirming |
| Progress Status | Status | In progress |
| Latest Progress | Text | 接口問題已解決，目前等待客戶確認 UI |
| Next Action | Text | 等待客戶回覆 UI 確認結果 |
| Blocker | Text | UI 尚未確認 |
| Owner | Text | Diego |
| Last Update | Last edited time | 2026-06-07 |
| Go-Live Date | Date | 2026-07-01 |

### Current Stage options
- Discovery
- Planning
- Implementation
- Testing
- Go-Live
- Post Go-Live

### Progress Status options
- Not started
- In progress
- Blocked
- Done

## 2. Issuer Progress History

| Property | Type | Example |
|---|---|---|
| Name | Title | Kpay - 2026-06-07 |
| Issuer | Relation | Issuer Progress Tracker |
| Change Date | Date | 2026-06-07 |
| Old Stage | Select | UI Confirming |
| New Stage | Select | SIT |
| Change Note | Text | UI 已確認，準備進 SIT |
| Next Action | Text | 安排 SIT 測試與確認交易流程 |
| Updated By | Text | Diego |

## 3. Issuer Notes

| Property | Type | Example |
|---|---|---|
| Title | Title | Kpay UI 確認會議 |
| Issuer | Relation | Issuer Progress Tracker |
| Note Type | Select | Meeting |
| Content | Text | 客戶確認 UI 文案可接受... |
| Source Date | Date | 2026-06-07 |
| Created By | Text | Diego |

> 第一版可以只建前兩張，第三張 `Issuer Notes` 可稍後再加。
