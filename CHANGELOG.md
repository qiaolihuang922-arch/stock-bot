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
- Owner 已在本輪明確要求「直接回填」後，使用 backfill CLI 逐檔執行 production write，且每檔 read-after-write 通過。

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
- `arch -arm64 .venv/bin/python scripts/backfill_daily_price_history.py --write --confirm-write --symbols <symbol> --years 2 --skip-existing --read-after-write`
  - 結果：12 檔逐檔 write-complete，read-after-write `status=ok`。
- `arch -arm64 .venv/bin/python scripts/research_trend_continuation.py --json`
  - 結果：completed；universe_count=12；total_hit_count=232；meets_min_sample_count=true；pullback_continuation_edge=positive。
- mutation / secret scan：
  - no schema mutation / live Telegram / secret assignment matches。

## 研究輸出摘要

- watchlist 12：3231、2421、3035、2303、3481、2344、2376、2408、2356、2324、2301、2337。
- production write：12 檔共新增 `daily_price` 5,218 rows。
- read-after-write row count：
  - 3231=485、2421=485、3035=485、2303=485、3481=478、2344=485、2376=485、2408=470、2356=485、2324=485、2301=464、2337=442。
  - 所有檔案日期範圍：2024-06-03..2026-06-03。
- 回填後 research：
  - total_hit_count：232。
  - per-symbol hits：2301=16、2303=22、2324=31、2337=23、2344=20、2356=19、2376=16、2408=8、2421=15、3035=16、3231=31、3481=15。
  - meets_min_sample_count：true（threshold=30）。
  - pullback continuation 5 日勝率 55.17%、5 日平均 +2.26%，結論 `positive`。
- 結論：階段一研究樣本門檻已達成，可另開階段二 major 策略設計任務；本輪仍未實裝正式買入路徑。

## 覆蓋層級

- CLI dry-run：covered。
- approved write helper：covered by fake client + `upsert_rows(..., client=...)` test。
- missing credentials fail-closed：covered。
- research artifact schema：covered。
- production actual write：covered by 12 檔逐檔 approved write + read-after-write artifact。
- 12 檔 full dry-run：未作 completion evidence；實際採逐檔 write/read-after-write，避免單次外部行情請求拖住全部。

## 殘留風險

- 本輪已實際寫 production `daily_price`；若需要回滾，需另開資料治理任務，不可手動亂刪。
- 雖然 pullback continuation 研究已 positive，extended spike 對照也為正，但本輪不授權追高或正式買入路徑。
- 階段二若啟動，仍需 major 策略設計、Owner 明確授權放開特定邊界，以及 official report replay / QA L3。

## 旁支待辦

- 另開階段二 major 任務：設計 `trend_continuation` 買入路徑，但僅限「回踩站回」且由 evidence gate 開關，不放寬 spike 追高。
- 階段二前需 Owner 明確授權是否放開 RESEARCH.md 既有「證據不得單獨變 BUY / 不得放寬追高」硬邊界中的特定例外。
