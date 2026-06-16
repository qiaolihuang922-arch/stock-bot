# CHANGELOG: cross_day_source_truth_v21_1_20260616

## 修改內容與檔案

- `services/cross_day_context.py`
  - 將 `daily_price` 加入 persistent cross-day source 白名單。
  - `build_cross_day_contexts` 讀取 `daily_price.stock_id/trade_date/close`。
  - 每檔輸出 `recent_daily_price_points`，只保存 DB 讀出的 close points。
- `core/generator.py`
  - 將 `daily_price` 加入 `PERSISTENT_CROSS_DAY_SOURCES`。
  - 新增 `persistent_recent_price_values(data)`。
  - `multi_day_rebound_needs_retest(data)` 不再讀 `data["closes"]` / `data["price"]`。
  - 多日反彈修復必須有 ready cross-day context 且 `source_of_truth` 包含 `daily_price`。
- `tests/test_cross_day_context.py`
  - 新增 `daily_price` 價格點會進 cross-day context 的測試。
- `tests/test_generator_report.py`
  - 新增沒有 DB context 時不得用 payload closes 觸發多日修復的負面案例。
  - 多日修復正面案例改為明確帶 `daily_price` context。
  - 綜合手機閱讀 replay 補上 DB context，避免舊測試繼續驗假跨日路徑。

## 契約影響

- 函式回傳:
  - `multi_day_rebound_needs_retest` 現在依賴 DB daily_price context。
  - `unheld_funnel_state` 不會因本次 payload closes 自行升級成 `等回測｜反彈修復待回測`。
- payload:
  - `cross_day_context.recent_daily_price_points` 新增可讀欄位。
- DB:
  - 無 schema change。
  - 無 write/backfill/prune。
  - 只有 read-only `daily_price` 查詢。
- message list:
  - 有 DB daily_price 最近點且符合條件時，仍可顯示 `反彈修復待回測`。
  - 沒有 DB daily_price 時，不能顯示多日修復升級。

## 版本同步

- Runtime 報文版本維持 `v21.1`。

## 直接消費者同步

- `formatTelegramMessages` / `unheld_funnel_state` tests 已更新。
- official `generate_report(dry_run=True)` 已驗，旺宏仍為 `等回測｜反彈修復待回測`，來源由 DB daily_price 支撐。

## 未影響模組

- 持倉停損 / 減碼 / 停利未改。
- DB schema / backfill / prune 未改。
- live Telegram 未觸發。
- 趨勢延續研究 artifact 未改；既有測試覆蓋缺 OHLCV rows 時 fail closed。

## 自檢命令與結果

- Targeted:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_cross_day_context.py tests\test_generator_report.py -q --tb=short -k "multi_day_weak_rebound or daily_price_points or weak_rebound or rebound"`
  - `3 passed`
- Broader strategy/report:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_cross_day_context.py tests\test_generator_report.py tests\test_analysis_engine.py tests\test_trend_continuation.py -q --tb=short`
  - `260 passed, 44 subtests passed`
- Evidence related:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_strategy_evidence.py tests\test_market_theme_evidence.py tests\test_volume_calibration.py -q --tb=short`
  - `53 passed, 13 subtests passed`
- Full:
  - `.\.venv\Scripts\python.exe -m pytest -q --tb=short`
  - `481 passed, 8 skipped, 108 subtests passed`
- Dry-run:
  - `generate_report(dry_run=True)`
  - 旺宏顯示 `等回測｜反彈修復待回測`
  - 報文不含 `淘汰｜弱反彈待確認`
- Production DB read-only:
  - `daily_price` 2337 recent rows:
    - 2026-06-15 close 159.0
    - 2026-06-12 close 146.5
    - 2026-06-11 close 140.0
    - 2026-06-10 close 135.0

## 覆蓋層級

- cross-day DB context: covered。
- strategy helper: covered。
- formatter/message list: covered。
- official generator dry-run: covered。
- production read-only source: covered。
- live Telegram: not run by design。

## 殘留風險

- 如果 production runner 仍顯示舊文案，優先查 runner commit / deployment path。
- PowerShell 中文 stdout 會 mojibake；測試與文件均以 UTF-8 檔案為準。
