# CHANGELOG:

## 修改內容

- 修正 `market_execution_bridge_lines()` 在 `market_mode == "進攻偏熱"` 時硬寫 `AI / 電子供應鏈仍偏多` 的 QA 阻塞。
- 只有既有輸入 `market_summary` 明確包含 `AI`、`人工智慧` 或 `電子供應鏈` 時，才保留 `主線：AI / 電子供應鏈仍偏多。`。
- 若 `market_summary` 沒有明確 AI / 電子供應鏈證據，即使市場為 `進攻偏熱`，summary 改輸出中性句 `主線：市場偏多但買點未成立。`。
- 將核心持倉摘要中的 `主線持倉保留` 改為中性風控語意，避免暗示所有持倉都是 AI 主線。
- 保持 `v20.0.12`，未改策略、DB、watchlist、Telegram payload shape 或 message order。

## 修改檔案

- `core/generator.py`
- `tests/test_generator_report.py`
- `CHANGELOG.md`

## 契約影響

- 使用者可見 Telegram 文案改變：
  - `進攻偏熱` 但缺少 AI / 電子供應鏈證據時，不再輸出 `AI / 電子供應鏈仍偏多`。
  - 核心持倉相關摘要不再使用 `主線持倉保留`。
- 未改函式回傳結構。
- 未改 message list 順序。
- 未改 Telegram payload shape。
- 未改報文分組、股票分類結果或 DB 寫入契約。

## 版本同步

- `core/generator.py` 維持 `VERSION = "v20.0.12"`。
- `tests/test_generator_report.py` 維持 v20.0.12 header 期望。
- 本輪為 v20.0.12 的 QA 阻塞修正，不升版、不回退。

## 直接消費者同步

- `formatTelegramSummary()` 已同步呼叫 `market_execution_bridge_lines(..., market_summary)`，讓 Telegram summary 使用既有 `market_summary` 判斷是否可輸出 AI / 電子供應鏈主線。
- `formatTelegramMessages()` 的 message list contract 未改，仍輸出持倉、未持倉、summary 三段。
- `tests/test_generator_report.py::GeneratorReportTest::test_intraday_v20_0_12_separates_mainline_from_execution` 已同步正向案例：`market_summary` 明確為 AI 主線時可保留 AI / 電子供應鏈句。
- `tests/test_generator_report.py::GeneratorReportTest::test_intraday_v20_0_12_hot_market_without_ai_evidence_uses_neutral_mainline` 已新增負面案例：非 AI 摘要、非 AI 標的且 `進攻偏熱` 時不得輸出 AI / 電子供應鏈。

## 未影響模組

- 未改 `services/analysis.py` 策略決策。
- 未改 `core/condition_engine.py` 條件映射。
- 未改行情來源。
- 未改 DB schema / migrations / Supabase write path。
- 未改 watchlist。
- 未改 replay/backfill。
- 未執行 live Telegram delivery。
- 未執行 live Supabase write。
- 未執行正式 backfill。

## 已跑自檢命令

- `PYTHONPATH=/private/tmp/stockbot_test_config:$PWD arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py::GeneratorReportTest::test_intraday_v20_0_12_separates_mainline_from_execution tests/test_generator_report.py::GeneratorReportTest::test_intraday_v20_0_12_hot_market_without_ai_evidence_uses_neutral_mainline -q`
  - 結果：`2 passed, 13 warnings`
- `PYTHONPATH=/private/tmp/stockbot_test_config:$PWD arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py -q`
  - 結果：`46 passed, 21 warnings`

## 殘留風險

- AI / 電子供應鏈保留條件目前只依既有 `market_summary` 明確文字判斷；未新增產業分類資料源，符合本輪禁止新增外部資料源與不改 watchlist 的限制。
- 未執行 full pytest、replay/backfill dry-run、live Telegram delivery 或 live Supabase write；依本輪禁止事項未執行。
