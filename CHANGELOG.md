# CHANGELOG: research_daily_price_backfill_and_trend_sample_expansion_20260603

## 任務尺寸與風險

- 任務類型：risk_patch / research。
- 風險原因：新增可寫 `daily_price` backfill CLI，但寫入必須走既有 approved interface；同時擴充 research artifact schema。
- 未碰：正式策略、Telegram 報文、DB schema / RLS / grant / policy / role / index / constraint、live Telegram。

## 修改內容

- 新增 `scripts/backfill_daily_price_history.py`
  - 支援 `--dry-run`、`--write`、`--confirm-write`、`--symbols`、`--start`、`--end`、`--years`、`--skip-existing`、`--read-after-write`、`--no-config`。
  - 未指定 symbols 時使用 `core.watchlist.WATCHLIST_CODES`，並要求 universe count = 12；否則 fail closed。
  - 市場資料來源使用既有 `services.stock_api.get_twse_ohlcv_history()`。
  - dry-run 不建立 write client、不寫入，輸出 `result: no-write`、per-symbol planned rows / rows_to_write。
  - write 需同時指定 `--write --confirm-write`；缺確認時 blocked。
  - write path 只呼叫既有 approved interface：`scripts.backfill_signals.upsert_rows(price_rows, signal_rows=[], client=...)`。
  - `--read-after-write` 讀回每檔 row count 與日期範圍，失敗則 blocked。
- 擴充 `scripts/research_trend_continuation.py`
  - 預設使用 watchlist 12 檔 universe；支援 `--symbols`、`--start`、`--end`。
  - artifact 新增 `universe_symbols`、`universe_count`、`date_range`、`pattern_definition`。
  - 新增 per-symbol `daily_price_rows_used`、`hit_count`、1/3/5/10 日 forward return count / avg / median。
  - 新增 aggregate `total_hit_count`、`threshold`、`meets_min_sample_count`、`blocked_reason`。
- 更新 `scripts/backfill_signals.py`
  - `upsert_rows()` 新增向後相容 `client=None` optional 參數，讓 backfill CLI 可注入 client 並仍走同一 helper。
- 新增 / 更新 tests
  - `tests/test_backfill_daily_price_history.py`
  - `tests/test_research_trend_continuation.py`
- 更新 research artifacts
  - `reports/research/trend_continuation_20260603.txt`
  - `reports/research/trend_continuation_20260603.json`
- 更新 `RESEARCH.md` 高信號摘要。

## 修改檔案

- `scripts/backfill_daily_price_history.py`
- `scripts/backfill_signals.py`
- `scripts/research_trend_continuation.py`
- `tests/test_backfill_daily_price_history.py`
- `tests/test_research_trend_continuation.py`
- `reports/research/trend_continuation_20260603.txt`
- `reports/research/trend_continuation_20260603.json`
- `RESEARCH.md`
- `TASK.md`

## 最小改動策略

- 僅新增 / 擴充研究與 backfill CLI。
- 不改正式策略檔：`services/analysis.py`、`core/condition_engine.py`、`core/generator.py`。
- 不新增 DB schema，不手寫普通 production DML。
- actual write 仍需要明確 CLI 參數與 production credentials；本輪未執行 production write。

## 契約影響

- 新增 CLI contract：`scripts/backfill_daily_price_history.py`。
- 擴充 research CLI artifact schema：`scripts/research_trend_continuation.py`。
- `scripts.backfill_signals.upsert_rows()` 新增 optional `client` 參數；既有呼叫不變。
- Telegram message list、strategy decision、DB schema、RR formula 未變。

## 直接消費者同步

- Owner / Architect 可用 backfill CLI dry-run 或實際回填。
- QA 可驗 dry-run no-write、missing credentials blocked、approved write helper、research artifact schema。
- 後續階段二只能讀 research artifact 判斷，不得直接從本輪開買入路徑。

## 未影響模組

- 未改 `services/analysis.py`。
- 未改 `core/condition_engine.py`。
- 未改 `core/generator.py`。
- 未改 Telegram delivery。
- 未改 DB schema / RLS / grant / policy / role / index / constraint。

## 已跑自檢命令

- `PYTHONPYCACHEPREFIX=/private/tmp/backfill_trend_pycache arch -arm64 .venv/bin/python -m py_compile scripts/backfill_daily_price_history.py scripts/research_trend_continuation.py scripts/backfill_signals.py tests/test_backfill_daily_price_history.py tests/test_research_trend_continuation.py tests/test_backfill_signals.py`
  - 結果：passed。
- `arch -arm64 .venv/bin/python -m pytest tests/test_backfill_daily_price_history.py tests/test_research_trend_continuation.py tests/test_backfill_signals.py -q`
  - 結果：15 passed。
- `arch -arm64 .venv/bin/python scripts/backfill_daily_price_history.py --dry-run --symbols 3231 --start 2026-06-01 --end 2026-06-02 --no-config`
  - 結果：dry-run no-write；planned_rows=2；live_write=false。
- `arch -arm64 .venv/bin/python scripts/backfill_daily_price_history.py --write --confirm-write --symbols 3231 --start 2026-06-01 --end 2026-06-02 --no-config`
  - 結果：exit 2 blocked；missing credentials；live_write=false。
- `arch -arm64 .venv/bin/python scripts/research_trend_continuation.py --json`
  - 結果：completed；universe_count=12；total_hit_count=5；meets_min_sample_count=false。
- mutation / secret scan：
  - no schema mutation / live Telegram / secret assignment matches。

## 研究輸出摘要

- watchlist 12：3231、2421、3035、2303、3481、2344、2376、2408、2356、2324、2301、2337。
- 目前 `daily_price` 每檔 rows_used：43。
- total_hit_count：5。
- per-symbol hits：2356=2、2376=2、2408=1，其餘 0。
- meets_min_sample_count：false（threshold=30）。
- 結論：尚未完成多年回填；不能進入階段二。

## 覆蓋層級

- CLI dry-run：covered。
- approved write helper：covered by fake client + `upsert_rows(..., client=...)` test。
- missing credentials fail-closed：covered。
- research artifact schema：covered。
- production actual write：not run。
- 12 檔 full dry-run network fetch：attempted but external market source call was too slow; not used as completion evidence.

## 殘留風險

- 12 檔多年 backfill 尚未實際寫入 production DB。
- 12 檔 full dry-run 受外部行情源速度影響，本輪未取得完整 12 檔 planned rows output；單檔 dry-run 與 focused tests 已覆蓋 contract。
- `get_twse_ohlcv_history()` 的 1-2 年可得性仍需實際 dry-run / write 時確認。
- Research artifact 仍顯示 total_hit_count=5，未達 30。

## 旁支待辦

- 執行 `scripts/backfill_daily_price_history.py --dry-run --years 2` 驗證 12 檔行情源可用性。
- Owner 確認後再執行 `--write --confirm-write --read-after-write`。
- 回填完成後重跑 `scripts/research_trend_continuation.py --json`，若 total_hit_count >=30 再另開階段二策略研究 / 實裝任務。
