# QA_REPORT: evidence per-stock reliability closeout

## 測試範圍

- 任務尺寸 / QA：major / L3。
- 驗證範圍：evidence score、modifier cap、market/theme fail-closed、per-stock strategy / market fallback、漏斗一致性、D1 資料不足文案、Phase 3 guard。
- 已讀：TASK.md、CHANGELOG.md、git diff、core/generator.py、presentation/report.py、tests/test_generator_report.py、tests/test_market_theme_evidence.py。
- 未要求 / 未執行：production DB read-only smoke、live Telegram、正式 backfill、production data quality matrix、full repo pytest。

## 關聯風險掃描

- VERSION 升至 v20.4.31，未回退。
- 未改 RR 公式、DB schema / RLS / grant / policy / role、production write path、approved write CLI、live Telegram、Phase 3 runner。
- per-stock evidence 缺 payload 時不再 fallback 到 report-level positive evidence。
- `source-error / missing-source / insufficient-data / unresolved-conflict` 先 fail closed，不再進 supporting / weak / mixed。
- supporting / partial modifier cap 成立；confirmed 才可到 ceiling。

## 跨區塊語意一致性

- `per_stock_evidence={"B": {}}` 且 report-level strategy_sample available / row_count=30 時，`compute_evidence_score("B")` 回 `score=None / status=unavailable`，modifier = 1.0。
- market/theme 逐股缺 payload 時同樣 fail closed，不偷吃 report-level confirmed trend。
- `unheld_tracking_only_count()` 已把 `隔日確認` 納入 `僅追蹤` aggregate。
- 漏斗拆分顯示 `隔日確認`，拆分加總 = `僅追蹤` 總數 = card actual。
- reliability 為資料不足時，報文改為 `短期背景資料不足，僅供觀察`；資料不足路徑不再輸出 `仍支持目前背景觀察`。

## 使用者誤讀風險

- 隔日確認現在歸在僅追蹤內並拆分顯示，避免使用者讀成「僅追蹤 0 但另有隔日確認 1」。
- 資料不足不再使用支撐語氣，避免讀成可加分或可行動。
- source-error / insufficient 不會顯示 supporting 或 +15%，避免把資料錯誤讀成證據支撐。

## 質疑與反證

- QA direct probe：`per_stock_evidence={"B": {}}` + report-level strategy_sample available / row_count=30 + manifest available，結果為 `score=None / status=unavailable / modifier=1.0`，strategy / market payload 皆 unavailable。
- `git diff --check`：passed。
- `pytest -q tests/test_generator_report.py -k ...`：10 passed。
- `pytest -q tests/test_market_theme_evidence.py -k ...`：7 passed。
- `pytest -q tests/test_phase3_evidence_automation.py tests/test_workflow_runtime_config.py`：20 passed。
- Combined targeted L3 suite：`tests/test_generator_report.py tests/test_market_theme_evidence.py tests/test_phase3_evidence_automation.py tests/test_workflow_runtime_config.py`：191 passed，225 warnings。

## 未測項目

- 未測 production DB read-only smoke、live Telegram、正式 backfill、production data quality matrix。
- 未跑 full repo pytest；本輪 L3 風險集中在 evidence/report/Phase3 guard，已跑相關 combined suite。
- warnings 為既有第三方 / Python deprecation，非本輪行為失敗。

## QA 結論

通過
