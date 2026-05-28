# CHANGELOG:

## 修改內容

- 將 Telegram 使用者可見版本由 `v20.0.12` 升為 `v20.0.13`。
- 同步 formatter header 相關測試期望為 `v20.0.13`。
- 新增 notifier 直接消費者測試，確認 `send_many()` 會把含 `v20.0.13` header 的 summary 保留在最後一則送出。
- 補強 evidence blocker 防回退：舊 `market_summary="AI / 電子供應鏈仍偏多"` 不能自我證明為 confirmed bullish；只有同時帶有 explicit evidence token 與 AI / 電子供應鏈關鍵字時，才輸出 `主線：AI / 電子供應鏈仍偏多。`
- 本輪是 `v20.0.13` QA blocker patch 修復，不是 `v20.1.0` 新能力發布。

## 修改檔案

- `core/generator.py`
- `tests/test_generator_report.py`
- `tests/test_notifier.py`
- `CHANGELOG.md`

## 契約影響

- 使用者可見 Telegram header 改為 `v20.0.13`。
- `core/generator.py` 的 `VERSION` 改為 `v20.0.13`。
- 未改 message list 順序，仍為持倉、未持倉、summary。
- 未改 Telegram payload shape。
- 未改 DB 寫入、DB schema、watchlist、scheduler 或 live delivery 行為。
- Evidence regression contract 保留：缺 explicit source / evidence token 時，不得把舊 market summary 轉成 AI / 電子供應鏈 confirmed bullish 語意。

## 版本同步

- `core/generator.py` 已同步 `VERSION = "v20.0.13"`。
- `tests/test_generator_report.py` 已同步 header 版本期望為 `v20.0.13`。
- `tests/test_notifier.py` 已新增 notifier 消費含 `v20.0.13` summary 的直接測試。
- 本輪未輸出或新增 `v20.1.0` 發布語意。

## 直接消費者同步

- Telegram 報文 header formatter：`formatTelegramSummary()` 使用的 `VERSION` 已升為 `v20.0.13`。
- Telegram message list formatter：`formatTelegramMessages()` 未改順序，summary 仍在最後一則。
- Notifier 直接路徑：`services/notifier.py::send_many()` 行為未改，測試已覆蓋含 `v20.0.13` header 的 summary 會作為最後一則送出。
- Formatter tests：版本 header 正向案例、include_detail summary header、evidence blocker 負面 fixture 已同步。

## 未影響模組

- 未改 `services/analysis.py` 策略 decision。
- 未改 `core/condition_engine.py` 條件映射。
- 未改 DB schema / migrations / Supabase write path。
- 未改 watchlist。
- 未改 replay/backfill。
- 未改 scheduler / cron。
- 未執行 live Telegram delivery。
- 未執行 live Supabase write。
- 未執行正式 backfill。

## 已跑自檢命令

- `PYTHONPATH=$PWD arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py::GeneratorReportTest::test_intraday_v20_0_12_separates_mainline_from_execution tests/test_generator_report.py::GeneratorReportTest::test_intraday_v20_0_12_hot_market_without_ai_evidence_uses_neutral_mainline tests/test_generator_report.py::GeneratorReportTest::test_intraday_v20_0_13_legacy_market_summary_cannot_confirm_theme -q`
  - 結果：`3 passed, 13 warnings`
- `PYTHONPATH=$PWD arch -arm64 .venv/bin/python -m pytest tests/test_notifier.py -q`
  - 結果：`3 passed`
- `PYTHONPATH=$PWD arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py tests/test_notifier.py -q`
  - 結果：`47 passed, 3 failed, 21 warnings`
  - 失敗項目：`test_rejected_weak_rr_uses_true_reject_reason_not_rr`、`test_telegram_messages_use_summary_cards_and_detail`、`test_today_buy_holding_overrides_add_level_in_all_summary_surfaces`
  - 失敗原因：這三項未固定 `get_market_phase()`，目前環境輸出 `明日觸發` / `明日未修復`，舊斷言期待 `盤中觸發` / `盤中觀察修復狀況`；不涉及本輪 `v20.0.13` 版本同步或 evidence blocker 變更。

## 殘留風險

- Evidence confirmed 判斷仍沿用本輪 patch 內的保守 token gate，未新增市場 / 題材 evidence provider、schema、cache 或外部資料源；這符合本輪不是 `v20.1.0` 新能力發布的限制。
- 完整 `tests/test_generator_report.py tests/test_notifier.py` broader smoke 有 3 個既有時間相位敏感測試失敗；本輪未修改該相位契約，需由後續任務決定是否將舊測試固定 phase。
- 未執行 full pytest、replay/backfill dry-run、live Telegram delivery 或 live Supabase write；依 `TASK.md` 禁止事項未執行。
