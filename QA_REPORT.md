# QA_REPORT: 修復證據 wiring 與 D2/B5 漏斗一致性

## 測試範圍

- 任務：`evidence-wiring-and-funnel-consistency-20260602`
- 任務尺寸 / QA：risk_patch / L3。
- 驗證範圍：strategy evidence 跨版本 outcomes、market/theme confirmed evidence trade_date wiring、official `generate_report(dry_run=True)` path、D2/B5 等冷卻 / 隔日確認 rendered message、VERSION 不升級。
- 未執行：production DB read-only smoke、full pytest、replay、backfill、live Telegram、production write。

## 關聯風險掃描

- `services/strategy_evidence.py` 移除 `daily_signal_snapshot.eq("version", version)` filter；未改 payload shape、DB write、schema / policy。
- `core/generator.py` 在 `build_report_context()` 傳入 `trade_date`，`market_theme_summary_evidence()` 對 string market_summary 也會以 `trade_date` 呼叫 confirmed evidence loader。
- `build_market_theme_production_trend_consumption_check()` fixture 顯示 `fresh_runner_rebuild=passed`、`uses_market_theme_confirmed_evidence_history=True`。
- `core/generator.py` 仍為 `VERSION = "v20.4.31"`；未升 `v20.4.32`。
- 未觸碰 `scripts/diagnose_evidence_sources.py`。

## 跨區塊語意一致性

- TASK / CHANGELOG / diff 同輪一致，修改檔案為 `core/generator.py`、`services/strategy_evidence.py`、`tests/test_strategy_evidence.py`、`tests/test_market_theme_evidence.py`、`tests/test_generator_report.py`。
- Strategy evidence 跨版本 fixture 可產生 `分類：RR不足｜樣本：10 筆`，不再因版本散落變 0 樣本。
- Market/theme official formatter path 消費 confirmed evidence trend，不只是 helper path。
- D2/B5 rendered message 內 `隔日確認 1、等冷卻 1` 與卡片 `智原=隔日確認`、`光寶科=等冷卻` 一致。

## 使用者誤讀風險

- QA official probe header：`【06/02 盤中｜v20.4.31】`。
- market/theme 顯示 `近 20 個交易日短期背景` 與 `近期 5 日支持仍支持目前背景觀察`，不再顯示 `短期背景資料不足，僅供觀察`。
- summary 顯示 `其中僅追蹤 2 檔拆分：隔日確認 1、等冷卻 1`。
- 未持倉卡片顯示 `【智原 3035】👀 隔日確認｜漲停反彈待確認` 與 `【光寶科 2301】⏳ 等冷卻｜過熱觀察`，未互換。

## 質疑與反證

- QA 不只重跑 Tech 自檢，另補 official `generate_report(dry_run=True)` probe，mock 正式入口依賴，驗證 loader `trade_date`、confirmed trend rendering、VERSION 與 D2/B5 手機閱讀一致性。
- `pytest targeted 4 tests`：4 passed，13 warnings。
- QA official generate_report probe：passed，`loader_calls=['2026-06-02']`。
- `build_market_theme_production_trend_consumption_check` fixture：`fresh_runner_rebuild=passed`、`uses_market_theme_confirmed_evidence_history=True`。
- `git diff --check`：passed。

## 未測項目

- 未跑 full pytest。
- 未做 production DB read-only smoke；production 資料品質與長期樣本分布仍需另開資料品質 / source-of-truth 任務。
- 未做 replay/backfill/live Telegram。
- 未驗所有 D2/B5 邊界分類，只驗 Owner 指定 `等冷卻 / 隔日確認` 混淆路徑。

## QA 結論

通過
