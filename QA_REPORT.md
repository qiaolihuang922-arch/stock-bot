# QA_REPORT:

## 測試範圍

- 任務：`today_buy_all_risk_summary_wording_20260608`。
- 範圍：盤後 Summary / 今日買入狀態 / Owner failure specimen 等價 dry-run。
- 未跑 live Telegram。

## 關聯風險掃描

- 原邏輯只看今日有買入事件，未區分買入後是否已停損 / 減碼。
- 市場行第一段其實已顯示 `今日已買 5（已風控 5）`，但結論與明細的 `已建立新倉` 造成跨行語意衝突。
- 修正只改 Summary wording 分流，不碰策略或 DB 狀態機。

## 跨區塊語意一致性

- 全部今日買入已風控時：
  - 市場行：`今日已買 N（已風控 N）`
  - 結論：`今日已買 N 檔，已全部轉入風控/停損減碼`
  - 明細：`今日買入後風控：N 檔`
- 新增有效進場仍獨立顯示為 `無` 或需開盤前確認。
- 持倉風控檢查仍列出停損 / 減碼主行動。

## 使用者誤讀風險

- 修正後不再把全數已風控的今日買入稱作「已建立新倉」。
- 純 `NEW_POSITION_RISK_WATCH` 的今日買入仍可被描述為已建立新倉，避免把尚未轉弱的今日買入錯寫成已停損減碼。

## 失敗標本反證

- Owner 標本等價 dry-run 反證：
  - 修正前：`結論：今日交易已建立新倉 5 檔；新增有效進場：無。`
  - 修正後：`結論：今日已買 5 檔，已全部轉入風控/停損減碼；新增有效進場：無。`
  - 修正後：`今日買入後風控：5 檔（英業達、智原、建準、聯電、旺宏）`

## 質疑與反證

- Regression 覆蓋同日買入後一檔停損、一檔減碼，確認不出現 `今日交易已建立新倉 2 檔`。
- 既有今日買入純觀察路徑仍通過，確認沒有把全部今日買入都改成風控。
- `generate_report(dry_run=True)` 使用 official generator 產出本輪 Summary，未使用 live Telegram。

## 未測項目

- 未做 live Telegram delivery。
- 未跑完整 `tests/test_generator_report.py` 全檔，因歷史狀態記錄該檔有 legacy snapshot 風險；本輪跑聚焦 regression 與 py_compile。
- 未改或驗證 GitHub runner schedule。

## QA 結論

通過。

本輪已沿 Owner 貼出的 final report 層反證，修正後 Summary 不再把 `今日已買 5（已風控 5）` 說成「已建立新倉」。
