# CHANGELOG: strategy_buy_path_db_replay_audit_v21_1_20260616

## 修改內容與檔案

- `scripts/audit_strategy_buy_path_replay.py`
  - 新增 Supabase `daily_price` read-only replay。
  - 對每個交易日、每檔 watchlist 重算 `analyze_ohlcv_snapshot`。
  - 同時計算 snapshot 原始 `is_tradeable` 與正式 `unheld_funnel_state`。
  - 統計狀態分布、主要 blocker、`等回測` 下一狀態、false negative。
- `tests/test_strategy_buy_path_replay.py`
  - 驗證 `等回測` 下一狀態統計。
  - 驗證 artifact read-only 欄位與 deadlock / false-negative diagnosis。
- `reports/audit/strategy_buy_path_replay_v21_1_20260616.json`
  - 產出本輪 replay artifact。

## 契約影響

- 新增審計工具，不改正式策略。
- DB:
  - read-only select from `daily_price`。
  - 無 schema change。
  - 無 write/backfill/prune。
- Telegram:
  - 未改報文。
  - 未 live delivery。

## 版本同步

- Runtime 報文版本維持 `v21.1`。

## 直接消費者同步

- Owner / Architect 可用 artifact 判斷策略是否卡死。
- Production runner 不受影響。

## 未影響模組

- `core/generator.py` strategy/funnel 未改。
- `services/analysis.py` 策略計算未改。
- `presentation/report.py` 未改。

## 自檢命令與結果

- Targeted tests:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_strategy_buy_path_replay.py tests\test_dry_run_replay.py -q --tb=short`
  - result: `6 passed, 1 warning`
- Full:
  - `.\.venv\Scripts\python.exe -m pytest -q --tb=short`
  - result: `486 passed, 8 skipped, 165 warnings, 110 subtests passed`
- DB replay:
  - `.\.venv\Scripts\python.exe scripts\audit_strategy_buy_path_replay.py --lookback-days 730 --version v21.1 --output reports\audit\strategy_buy_path_replay_v21_1_20260616.json`
  - result:
    - events: `5798`
    - stocks: `12`
    - buyable_or_trend_days: `700`
    - buy_like_days_including_prepare: `1035`
    - snapshot_tradeable_blocked_by_funnel_days: `0`
    - deadlock_suspected: `false`

## 覆蓋層級

- production DB read-only: covered via `daily_price` replay。
- helper/script: covered。
- formal generator message rendering: not changed in this cycle。
- live Telegram: not run by design。

## 殘留風險

- Replay is daily-close based; it does not simulate intraday fill quality or actual order execution.
- Replay assumes source availability because it recomputes from `daily_price`; source manifest failures are a separate production-source audit.
- `等回測` only transitions to `可買` in a minority of cases; this is expected and documented by artifact.
