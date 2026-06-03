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
- Production actual write：未執行。
- Telegram：未改、未 live send。
- Strategy decision：未改 `services/analysis.py`、`core/condition_engine.py`、`core/generator.py`。
- Credential exposure：blocked output 不含 token / DSN / secret value。

## 跨區塊語意一致性

- `TASK.md` 要求 watchlist 12；實作使用 `core.watchlist.WATCHLIST_CODES`，本地確認 count=12。
- `RESEARCH.md`、artifact、CHANGELOG 結論一致：目前每檔 rows_used=43、total_hit_count=5、未達 30。
- Backfill CLI 明確區分 dry-run 與 write；write 需 `--confirm-write`。

## 使用者誤讀風險

- 本輪沒有開策略買路，也沒有說 trend continuation 有 edge。
- `extended_spike` 在舊 artifact 中表現為正，但本輪仍只是對照，不是追高授權。
- Backfill CLI 可以實際寫 DB，但本輪沒有執行 production write；需要 Owner 另行確認後跑。
- 12 檔 full dry-run 被外部行情源拖慢，本輪不能宣稱已完整拿到 12 檔 planned rows。

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
  - `aggregate.total_hit_count=5`。
  - `aggregate.meets_min_sample_count=false`。

## 質疑與反證

- 質疑：是否手寫 production DML？
  - 反證：新 CLI 呼叫 `scripts.backfill_signals.upsert_rows(price_rows, signal_rows=[], client=...)`；未直接在新 CLI 中呼叫 `daily_price.upsert`。
- 質疑：是否改了正式策略？
  - 反證：diff 未包含 `services/analysis.py`、`core/condition_engine.py`、`core/generator.py`。
- 質疑：是否已完成多年樣本擴充？
  - 反證：research artifact 仍顯示每檔 rows_used=43、total_hit_count=5；沒有完成 production backfill。

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
  - 結果：completed，universe_count=12，total_hit_count=5。

## 未測項目

- 未跑 full pytest。
- 未做 production actual write。
- 未完成 12 檔 full dry-run，因外部行情源呼叫超時偏慢而中止。
- 未改 / 未驗正式 Telegram 報文。
- 未接階段二策略。

## QA 結論

conditional pass

理由：CLI contract、approved helper path、fail closed、research artifact schema 已驗；但本輪未實際回填 production daily_price，也未取得完整 12 檔 dry-run output。因此只能說「工具已就緒、目前研究樣本仍不足」，不能說多年樣本已補齊或階段二可開始。
