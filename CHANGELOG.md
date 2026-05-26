# CHANGELOG

## 2026-05-26 - v20.0 Strategy Evidence Foundation

狀態：已完成並推送。  
Commit：`2cc4e8a feat: add v20 strategy evidence foundation`

## 修改內容

- 新增 `services/strategy_evidence.py`，提供策略證據資料層：
  - market daily bars。
  - strategy feature snapshots。
  - outcome metrics。
  - classification audit。
  - classification report / Telegram evidence summary。
- 新增 `docs/v20_strategy_evidence_schema.sql`，作為 production schema 草案。
- `core/generator.py`：
  - 版本升至 `v20.0`。
  - Telegram summary 增加 `📊 策略證據 v20.0`。
  - evidence 寫入 / 查詢失敗時降級為略過文字，不阻斷主報文。
- `scripts/dry_run_replay.py`：
  - validate 時輸出 strategy evidence feature rows。
- `scripts/backfill_signals.py`：
  - dry-run 顯示 evidence tables row counts。
  - write 模式支援 evidence upsert，但仍需既有 `--write --confirm-write`。
- 新增 / 更新測試：
  - `tests/test_strategy_evidence.py`
  - `tests/test_generator_report.py`
  - `tests/test_backfill_signals.py`

## 未影響模組

- `services/analysis.py`
- `core/signal_snapshot.py`
- `core/signal_validator.py`
- `services/daily_snapshot_store.py`
- `services/signal_store.py`
- `services/position_store.py`
- `services/notifier.py`
- `services/stock_api.py`
- `core/watchlist.py`
- Supabase Edge Function
- BUY / SELL / WAIT 決策門檻
- RR / 過熱 / 漲停不追 / 停損 / 停利 / 加碼硬門檻
- `decision / action / is_tradeable / is_best_candidate` 策略輸出

## 已執行驗證

- `.venv/bin/python -m pytest`
  - `99 passed, 21 warnings`
- `.venv/bin/python scripts/dry_run_replay.py --dry-run --validate --source synthetic --version v20.0 --start-date 2026-05-18 --end-date 2026-05-22`
  - `VALIDATION OK`
  - `STRATEGY EVIDENCE FEATURE ROWS: 60`
- `.venv/bin/python scripts/backfill_signals.py --dry-run --source synthetic --version v20.0 --start-date 2026-05-18 --end-date 2026-05-22`
  - `VALIDATION OK`
  - `market_daily_bars rows: 60`
  - `strategy_feature_snapshots rows: 60`
  - `strategy_outcome_metrics rows: 72`
  - `strategy_classification_audit rows: 0`
  - `DRY RUN ONLY: no database writes`

## 未執行

- production schema apply。
- live Supabase write。
- live Telegram delivery。
- TWSE live replay / live backfill。
- 正式 backfill write。

以上需 Owner 另開明確批准流程。
