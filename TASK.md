# TASK: docs_local_env_cleanup_20260626

## 任務狀態

- task_id: `docs_local_env_cleanup_20260626`
- 任務類型: `tiny_patch`
- 狀態: `QA_passed_pushed`
- 版本建議: `v21.1`
- QA 分級: `L1`

## Owner 問題

整理 Markdown，去除過期或重複資訊，並把 D 槽本地部署流程集中優化到部署文件。

## 使用者可見結果

- 根目錄 handoff 文件只保留當前狀態、必要證據與下一步。
- D 槽安裝/啟動流程在 `tools/cao_agent/DEPLOYMENT.md` 可直接照做。
- 不改產品代碼、不改策略、不發 Telegram、不動 DB。

## 影響模組與直接消費者

- Markdown 文件與 CAO local env bootstrap。
- 直接消費者: Owner、新對話 Architect、後續本機部署流程。

## 驗收條件

- UTF-8 讀取固定 Markdown 無 mojibake。
- Architect scope gate pass。
- D 槽 bootstrap smoke pass。
- Git completion / closeout gates pass after commit and push。

## 禁止事項

- 不刪固定 8 份 Markdown。
- 不刪歷史 handoff/evidence docs。
- 不碰產品程式碼、測試邏輯、production DB 或 live Telegram。
