# CHANGELOG:

## 修改內容

- 新增 `build_market_theme_evidence()`，把 `results_map`、`watchlist_groups`、formatter report input 統一視為 `report_derived` source family，不能互相湊成 confirmed。
- confirmed 判斷改為只計入完整 structured source：必須具備 `as_of`、`freshness`、`confidence`、`supports_claims`、`limitations`，且需至少兩個不同 source family。
- 同一個 `source_family` 多筆 structured source 只計一次；缺欄位 source 不計入 confirmed。
- Telegram summary 只在 helper 回傳 confirmed 且 `theme_direction == bullish` 時顯示 AI / 電子供應鏈偏多；report-derived only 改顯示 `weak｜來源不足｜只追蹤` 與不可買語意。
- confirmed market theme 只影響市場主題顯示，不放寬個股買點；買點未成立時 summary 仍顯示 `新倉：無有效進場` / 僅追蹤。
- 使用者可見 header / `VERSION` 已核對並同步為 `v20.1.0`。

## 修改檔案

- `core/market_theme_evidence.py`
- `core/generator.py`
- `tests/test_market_theme_evidence.py`
- `tests/test_generator_report.py`
- `tests/test_notifier.py`
- `CHANGELOG.md`

## 契約影響

- 新增 public helper `core.market_theme_evidence.build_market_theme_evidence()`，回傳 market theme evidence dict，包含 `theme_status`、`theme_direction`、`theme_label`、`actionability`、`source_families`、`confirmed_source_families`、`source_family_count_for_confirmed`、`limitations`、`confirmed`。
- 新增 formatter helper `format_market_theme_summary_lines()`，供 Telegram summary 呈現 confirmed / weak / absent。
- `formatTelegramSummary()` 的使用者可見內容新增市場主題行；無主題時不新增內容，report-derived only 時顯示 weak，不顯示 confirmed。
- `ai_supply_chain_mainline_supported()` 不再從 legacy 字串 token 判斷 confirmed；只有 dict evidence 明確 confirmed bullish 才允許偏多主線文案。
- Telegram message list 順序、Telegram payload shape、notifier `send_many()` 介面、DB schema、DB payload、watchlist、scheduler、策略 decision 均未改。

## 版本同步

- `core/generator.py` 已同步 `VERSION = "v20.1.0"`。
- `tests/test_generator_report.py` header 期望已同步為 `v20.1.0`。
- `tests/test_notifier.py` notifier 直接消費者測試已同步含 `v20.1.0` header 的 summary。

## 直接消費者同步

- Telegram summary formatter：已改用 `build_market_theme_evidence()` 判斷 weak / confirmed 顯示，report-derived only 不再輸出 confirmed 或 AI/電子供應鏈偏多。
- Telegram message list / notifier dry-run output：`formatTelegramMessages()` 仍將 summary 放在最後一則；`tests/test_notifier.py` 確認最後一則 header 版本保留。
- generate_report production 預設路徑：目前未接入 structured market theme source，預設只能產生 absent；若既有結果或 formatter input 只提供 theme 字串，最多產生 weak，不會產生 confirmed。
- QA helper / formatter tests：新增 `tests/test_market_theme_evidence.py` 覆蓋 report-derived only、缺 structured 欄位、同 family 重複、完整 market_state + structured_strategy_evidence、Telegram weak 顯示、confirmed 但買點未成立。

## 未影響模組

- 未改 `services/analysis.py` 策略 decision。
- 未改 `core/condition_engine.py` 條件映射。
- 未改行情來源與 `get_market_phase()` 判斷邏輯。
- 未新增 DB table / migration。
- 未改 DB write path / payload schema。
- 未改 watchlist。
- 未改 scheduler / cron。
- 未改 replay/backfill。
- 未執行 live Telegram delivery。
- 未執行 live Supabase write。
- 未執行正式 backfill。

## 已跑自檢命令

- `arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence.py tests/test_generator_report.py tests/test_notifier.py`
  - 結果：`59 passed, 21 warnings`。

## 殘留風險

- 本輪只完成 market theme evidence contract 與 Telegram 呈現收斂，未接線真正 structured provider、DB schema、cache、backfill 或 live delivery。
- `strategy_evidence_summary` 仍只是既有字串 summary；本輪沒有宣稱它已自動接入 structured confirmed。
- production `generate_report()` 尚未提供 `market_state` / `structured_strategy_evidence` structured source，因此 confirmed 只能由明確傳入的 dict evidence 或 helper 測試 fixture 驗證。
- 測試需用 `arch -arm64 .venv/bin/python` 執行；直接 `pytest` 可能不在 PATH，直接 `.venv/bin/python` 在此環境曾有架構不符風險。
