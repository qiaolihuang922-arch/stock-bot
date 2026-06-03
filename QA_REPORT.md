# QA_REPORT:

## 測試範圍

本輪 TASK 為 risk_patch / L3。驗證範圍聚焦 Owner 指定的 evidence source / modifier / daily evidence runner / 使用者可見報文，不擴成 full repo、live Telegram、production backfill 或 production write。

已核對：

- TASK.md
- CHANGELOG.md
- git diff --stat / git diff --name-status
- core/generator.py
- scripts/run_phase3_evidence_automation.py
- .github/workflows/stock-bot.yml
- tests/test_generator_report.py
- tests/test_phase3_evidence_automation.py
- tests/test_workflow_runtime_config.py

可吸收 diff：

- .github/workflows/stock-bot.yml
- CHANGELOG.md
- QA_REPORT.md
- TASK.md
- core/generator.py
- scripts/run_phase3_evidence_automation.py
- tests/test_generator_report.py
- tests/test_phase3_evidence_automation.py
- tests/test_workflow_runtime_config.py

## 風險預算與停止條件

1. per-stock strategy evidence 仍吃 global classification，導致 sample 36/38 仍 partial。
   - 停止條件：緯創 / 華邦等價 fixture 無法在 global row_count=3 時依自身 backtest_context 進 ready，或 final_confidence 仍等於 technical_confidence。
2. market daily evidence runner 缺 payload 或舊 trade_date payload 時仍靜默成功。
   - 停止條件：缺 MARKET_THEME_APPROVED_PAYLOAD 仍 exit 0，或 payload trade_date mismatch 仍進 write path。
3. 弱勢 / 失敗 / 過熱股被 evidence 背景抬分，或過熱 RR 數值外漏。
   - 停止條件：decision=FAIL / FAILED_BREAKOUT modifier > 1.0，或過熱 hard blocker 被放寬。

## 關聯風險掃描

- core/generator.py 仍為 VERSION = "v20.4.34"，未回退。
- per-stock strategy evidence 現在可從各股 backtest_context 取得 sample/reference，sample >= 10 且參考度高時可進 ready。
- apply_evidence_confidence 仍保留弱勢 / FAIL / FAILED_BREAKOUT / WEAK / DISTRIBUTION / EXTREME 護欄，不允許正向 boost。
- workflow cron 已由 `25 5 * * 1-5` 改為 `0 6 * * 1-5`，對應台北收盤後。
- Phase 3 runner 新增 `--require-market-theme-payload`；缺 approved payload 時 fail closed；payload trade_date mismatch 會在 write CLI 前失敗。
- 未見 RR 公式、DB schema、live Telegram、production write path、持倉狀態機 diff。

## 跨區塊語意一致性

- per-stock replay passed：global strategy row_count=3 時，緯創 sample 36、華邦 sample 38 仍進 ready，兩股 modifier 不同，final != technical。
- low sample / no history path passed：低樣本 partial，無 backtest unavailable，不偽造 ready。
- weak / failed path passed：聯電等價 FAILED_BREAKOUT fixture modifier <= 1.0，不被背景抬分。
- overheat / RR hard blocker 既有回歸 passed：confirmed evidence 不放寬過熱和 RR hard blockers。
- Phase 3 runner path passed：缺 payload fail closed、舊 trade_date payload 不進 write、workflow step 帶 `--require-market-theme-payload`。

## 使用者誤讀風險

- 已反證「回測樣本 36/38 但 evidence partial +0%」：official message-list fixture 顯示 `綜合 84｜技術 78｜證據 +8%（supporting）`，且不含該卡 `證據：partial｜僅輔助參考`。
- 已反證「證據抬高弱勢 / 失敗股」：FAILED_BREAKOUT fixture modifier <= 1.0。
- RR / 防抖 / summary count 本輪主要依賴既有契約與既有回歸，未新增策略方向；本輪未改 RR 公式。
- market daily freshness 的使用者可見完成口徑仍缺 production/read-only artifact：目前只能證明 runner 會在缺 payload / 舊 payload 時 fail closed，不能證明 2026-06-03 production row 已存在。

## 質疑與反證

- 質疑：Tech 是否只修 helper，沒有打到 official message-list？
  - 反證：`tests/test_generator_report.py::GeneratorReportTest::test_per_stock_backtest_context_drives_strategy_ready_when_global_sample_partial` 通過，覆蓋 `formatTelegramMessages()` rendered card。
- 質疑：daily_evidence 是否仍在收盤前跑？
  - 反證：workflow runtime test 通過，cron 斷言為 `0 6 * * 1-5`。
- 質疑：缺 MARKET_THEME_APPROVED_PAYLOAD 是否仍靜默 skip？
  - 反證：`test_main_requires_market_theme_payload_when_gate_enabled` 與 `test_phase3_evidence_step_fails_closed_without_market_theme_payload_secret` 通過，缺 payload exit 2。
- 質疑：舊日期 approved payload 是否可能寫入當日？
  - 反證：`test_market_theme_payload_trade_date_mismatch_fails_before_write` 通過，runner 在 write 前擋下 mismatch。

## 已跑命令

- `arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py tests/test_phase3_evidence_automation.py tests/test_workflow_runtime_config.py`
  - 結果：179 passed，241 warnings。
- `PYTHONPYCACHEPREFIX=/private/tmp/evidence_score_effective_pycache arch -arm64 .venv/bin/python -m py_compile core/generator.py scripts/run_phase3_evidence_automation.py tests/test_generator_report.py tests/test_phase3_evidence_automation.py tests/test_workflow_runtime_config.py`
  - 結果：passed。
- `git diff --check`
  - 結果：passed。

## 未測項目

- 未跑 live Telegram。
- 未跑 production write / backfill。
- 未讀 production DB，也沒有 safe read-only artifact；因此未證明 market_theme_confirmed_evidence 已存在 2026-06-03 row。
- 未驗真實 GitHub Actions run artifact；目前只驗 workflow script 與 local runner fixture。
- 未跑 full repo pytest；本輪按 L3 直接消費者與 risk path 跑 generator + Phase3 + workflow 相關測試。

## QA 結論

conditional pass
