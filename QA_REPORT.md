# QA_REPORT: research_daily_price_backfill_and_trend_sample_expansion_20260603

## 測試範圍

- 任務：`research_daily_price_backfill_and_trend_sample_expansion_20260603`
- QA 分級：L3。
- 已驗：
  - backfill CLI dry-run no-write。
  - approved write helper contract。
  - missing credentials fail closed。
  - research artifact 12 檔 universe / per-symbol / aggregate schema。
  - 未改正式策略核心檔。

## 關聯風險掃描

- DB schema / write path：未新增 schema；write path 走既有 `scripts.backfill_signals.upsert_rows(...)`。
- Production actual write：Owner 明確要求「直接回填」後已執行；12 檔逐檔 write-complete，read-after-write ok。
- Telegram：未改、未 live send。
- Strategy decision：未改 `services/analysis.py`、`core/condition_engine.py`、`core/generator.py`。
- Credential exposure：blocked output 不含 token / DSN / secret value。

## 跨區塊語意一致性

- `TASK.md` 要求 watchlist 12；實作使用 `core.watchlist.WATCHLIST_CODES`，本地確認 count=12。
- `RESEARCH.md`、artifact、CHANGELOG 結論一致：回填後 total_hit_count=232、meets_min_sample_count=true、pullback edge positive，但未接正式策略。
- Backfill CLI 明確區分 dry-run 與 write；write 需 `--confirm-write`。

## 使用者誤讀風險

- 本輪沒有開策略買路；回填後 trend continuation 研究顯示 positive edge，但這只支持另開階段二設計任務，不等於已授權正式買入。
- `extended_spike` 在舊 artifact 中表現為正，但本輪仍只是對照，不是追高授權。
- Backfill CLI 已實際寫 DB；本輪完成後不可再把「未寫入」當成現況。
- 12 檔 full dry-run 被外部行情源拖慢；實際採逐檔 write/read-after-write 完成。

## 失敗標本反證

- missing credentials：
  - `--write --confirm-write --no-config` 回傳 `status=blocked`、`fail_closed_reason=missing-credentials`、`live_write=false`、exit 2。
- dry-run no-write：
  - 單檔 dry-run 回傳 `result=no-write`、`live_write=false`、planned_rows / rows_to_write。
- approved write helper：
  - fake client test 觀察到 `daily_price.upsert(..., on_conflict="stock_id,trade_date")` 由 `scripts.backfill_signals.upsert_rows(..., client=...)` 觸發。
- research artifact：
  - `universe_count=12`。
  - `per_symbol_count=12`。
  - `aggregate.total_hit_count=232`。
  - `aggregate.meets_min_sample_count=true`。
- production write / read-after-write：
  - 12 檔合計新增 5,218 rows。
  - 每檔 row_count 442-485，日期範圍皆為 2024-06-03..2026-06-03。

## 質疑與反證

- 質疑：是否手寫 production DML？
  - 反證：新 CLI 呼叫 `scripts.backfill_signals.upsert_rows(price_rows, signal_rows=[], client=...)`；未直接在新 CLI 中呼叫 `daily_price.upsert`。
- 質疑：是否改了正式策略？
  - 反證：diff 未包含 `services/analysis.py`、`core/condition_engine.py`、`core/generator.py`。
- 質疑：是否已完成多年樣本擴充？
  - 反證：12 檔 read-after-write 均為 2024-06-03..2026-06-03；research artifact source_rows=5734、total_hit_count=232。
- 質疑：positive edge 是否等於可以直接改策略？
  - 反證：TASK 非目標明確禁止開正式買入路徑；本輪沒有改 `services/analysis.py`、`core/condition_engine.py`、`core/generator.py`。

## 已跑命令

- `PYTHONPYCACHEPREFIX=/private/tmp/backfill_trend_pycache arch -arm64 .venv/bin/python -m py_compile scripts/backfill_daily_price_history.py scripts/research_trend_continuation.py scripts/backfill_signals.py tests/test_backfill_daily_price_history.py tests/test_research_trend_continuation.py tests/test_backfill_signals.py`
  - 結果：passed。
- `arch -arm64 .venv/bin/python -m pytest tests/test_backfill_daily_price_history.py tests/test_research_trend_continuation.py tests/test_backfill_signals.py -q`
  - 結果：15 passed。
- `arch -arm64 .venv/bin/python scripts/backfill_daily_price_history.py --dry-run --symbols 3231 --start 2026-06-01 --end 2026-06-02 --no-config`
  - 結果：no-write dry-run。
- `arch -arm64 .venv/bin/python scripts/backfill_daily_price_history.py --write --confirm-write --symbols 3231 --start 2026-06-01 --end 2026-06-02 --no-config`
  - 結果：blocked / missing credentials / exit 2。
- `arch -arm64 .venv/bin/python scripts/research_trend_continuation.py --json`
  - 結果：completed，universe_count=12，total_hit_count=232，meets_min_sample_count=true，pullback edge positive。
- `arch -arm64 .venv/bin/python scripts/backfill_daily_price_history.py --write --confirm-write --symbols <symbol> --years 2 --skip-existing --read-after-write`
  - 結果：12 檔逐檔 write-complete，read-after-write ok。
- read-only row count probe：
  - 結果：12 檔 row_count 442-485，日期範圍 2024-06-03..2026-06-03。

## 未測項目

- 未跑 full pytest。
- 未做 DB rollback 驗證。
- 未完成單次 12 檔 full dry-run，因外部行情源呼叫超時偏慢而中止；改用逐檔 write/read-after-write。
- 未改 / 未驗正式 Telegram 報文。
- 未接階段二策略。

## QA 結論

conditional pass

理由：approved write path、12 檔 production write、read-after-write、research artifact schema 已驗；研究樣本已達 30+ 且 edge positive。但本輪仍未改正式策略，也未取得階段二 Owner 授權，所以只能說「階段一研究可支持另開階段二設計」，不能說正式買入路徑已完成。
