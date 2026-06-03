# CHANGELOG: Render market/theme evidence freshness check 與幂等補寫

## 任務尺寸與風險

- 任務類型：risk_patch。
- 風險原因：本輪改 Render / runner 啟動前置檢查、market/theme production evidence approved write path、read-after-write fail-closed 與 backfill workflow / CLI。
- 未改：DB schema、RR 公式、策略決策、Telegram 報文內容、live delivery。

## 修改內容

- `scripts/run_phase3_evidence_automation.py` 新增 freshness-only 流程：
  - 預設檢查最近 5 個 confirmed trading days。
  - safe write time 預設台北 14:00，可用 CLI/env 覆寫。
  - 逐日檢查 `market_theme_confirmed_evidence` 與 `market_theme_index_daily_bars`。
  - 已完整日期輸出 `already-complete` 並跳過 upsert。
  - 未到安全時間輸出 `skipped-before-safe-write-time`，只讀不寫。
  - 已到安全時間且缺失時，走既有 `backfill_market_theme_sources.py` / `upsert_source_payloads()` approved interface，寫後再 read-after-write。
  - read、upsert、read-after-write mismatch、preflight exception 都輸出 `MARKET_THEME_FRESHNESS_FAILED ... action=fail_closed` 並讓 CLI 非 0。
  - freshness log/report 增加流程版本 `market_theme_freshness_v1`。
- `market_theme_confirmed_evidence` 完整性改為必須覆蓋 9 個官方 TWSE 題材 key；部分 rows 不算完整，會觸發補寫。
- `app.py` 在 Render route dispatch GitHub workflow 前執行 freshness preflight；失敗時不 dispatch，也不寫 already-sent tag，保留 5 分鐘後重試機會。
- `scripts/backfill_market_theme_sources.py` 改為顯式 `--trade-date` 或 `--start-date/--end-date` 決定驗證範圍；錯誤文案不再 May-only。
- `.github/workflows/stock-bot.yml` 的 market/theme backfill step 同步傳入 `start_date/end_date` 並使用 `--historical-range`。

## 修改檔案

- `.github/workflows/stock-bot.yml`
- `app.py`
- `scripts/backfill_market_theme_sources.py`
- `scripts/run_phase3_evidence_automation.py`
- `tests/test_app_render_preflight.py`
- `tests/test_market_theme_source_backfill.py`
- `tests/test_phase3_evidence_automation.py`
- `tests/test_workflow_runtime_config.py`

## 最小改動策略

- 不新增 DB schema 或新 source-of-truth。
- 不手寫 production DML。
- 不把 `2026-06-01~2026-06-03` 寫死在產品邏輯，只作為 backfill / probe 日期。
- 保留既有 approved upsert/read-after-write path，僅增加 Render 前置 freshness orchestration。

## 契約影響

- 新 CLI：
  - `scripts/run_phase3_evidence_automation.py --freshness-check-only`
  - `--freshness-lookback-days`
  - `--safe-write-time`
- 新 env：
  - `MARKET_THEME_FRESHNESS_LOOKBACK_DAYS`
  - `MARKET_THEME_SAFE_WRITE_TIME`
- 新 log / report version：
  - `market_theme_freshness_v1`
- Render route：
  - freshness preflight 成功後才檢查 already-sent 與 dispatch workflow。
  - freshness preflight 失敗時回傳 `freshness check failed`，不發 workflow，不寫送出 tag。
- Backfill CLI：
  - `--start-date/--end-date` 顯式控制 range。
  - `--trade-date` 單日 backfill 時 effective range 等於該日。

## 直接消費者同步

- Render 每 5 分鐘觸發的 `/` route 已接入 freshness preflight。
- GitHub workflow 手動 backfill step 已同步 `start_date/end_date`。
- Phase3 evidence CLI 保留既有 daily evidence path，新增 freshness-only mode，不影響 Telegram runner payload。

## 未影響模組

- 未改 `core/generator.py` Telegram 報文版本或格式。
- 未改 RR 計算。
- 未改 strategy decision / holding state machine。
- 未改 DB schema / RLS / grant / policy / role。
- 未執行 live Telegram。

## 已跑自檢命令

- `arch -arm64 .venv/bin/python -m pytest tests/test_app_render_preflight.py tests/test_phase3_evidence_automation.py tests/test_market_theme_source_backfill.py tests/test_workflow_runtime_config.py`
  - 結果：45 passed。
- `PYTHONPYCACHEPREFIX=/private/tmp/stock_bot_pycache_main arch -arm64 .venv/bin/python -m py_compile app.py scripts/run_phase3_evidence_automation.py scripts/backfill_market_theme_sources.py`
  - 結果：passed。
- `git diff --check`
  - 結果：passed。

## 覆蓋層級

- helper：recent confirmed trade dates、safe write time、complete / missing 判斷。
- interface：approved backfill function、read-after-write mismatch fail closed。
- runner：Render route freshness failure blocks dispatch and already-sent tag。
- workflow / CLI：backfill workflow uses `start_date/end_date` and `--historical-range`。
- production source：未在本輪測試中讀寫 production；6/1~6/3 已由 Architect 另用既有 script 實際補寫並 read-after-write passed。

## 殘留風險

- Render preflight 每次會執行最多 5 個交易日的 freshness checks；若 production read 或 TWSE calendar source error，會 fail closed 並暫停 dispatch，避免錯誤報文，但也可能造成短暫不發。
- `market_theme_index_daily_bars` 完整性目前要求 market row + 至少一個 sector theme row；若未來要跟 confirmed evidence 一樣嚴格覆蓋全部官方題材，需另開 tighten task。
- production DB 的實際 Render 環境需部署後看 runner log，確認 5 分鐘觸發下 latency 在 Render timeout 內。

## 旁支待辦

- 若 Render timeout 太短，需把 freshness preflight 拆成獨立 lightweight endpoint 或 background job，但仍保持「發報文前先看 freshness 狀態」。
- 若未來官方題材 key 變更，`EXPECTED_CONFIRMED_SECTOR_THEMES` 應改為從 backfill source map 派生，避免常量漂移。
