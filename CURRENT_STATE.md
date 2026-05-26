# CURRENT_STATE.md

本文件由 Architect 維護，作為專案短上下文。新會話應先讀本文件，再依任務讀必要摘要文件或局部源碼。

## 專案狀態

- 專案：台股策略報文機器人。
- 目前穩定線：`v20.0 Strategy Evidence Foundation` 已完成、QA L3 通過並推送。
- 最新 commit：`2cc4e8a feat: add v20 strategy evidence foundation`
- 交付形態維持不變：定時 GitHub Actions / 腳本 -> 產生 Telegram 報文 -> 發送給 Owner。
- 預設只處理 `core/watchlist.py` 的 12 檔股票。

## v20.0 已完成

- 新增 `services/strategy_evidence.py`：
  - market daily bars。
  - strategy feature snapshots。
  - outcome metrics。
  - classification audit。
  - classification report / Telegram evidence summary。
- 新增 `docs/v20_strategy_evidence_schema.sql` 作為 production schema 草案。
- `core/generator.py` 版本升至 `v20.0`，Telegram summary 新增 `📊 策略證據 v20.0`。
- `scripts/dry_run_replay.py` 新增 evidence feature rows 輸出。
- `scripts/backfill_signals.py` 新增 evidence row planning / optional upsert path；正式寫庫仍需 `--write --confirm-write`。
- 新增 / 更新測試覆蓋 evidence layer、Telegram summary、backfill evidence rows。

## v20.0 驗證

- QA L3 結論：通過。
- `.venv/bin/python -m pytest`：`99 passed, 21 warnings`。
- synthetic replay dry-run：`VALIDATION OK`，`STRATEGY EVIDENCE FEATURE ROWS: 60`。
- synthetic backfill dry-run：`VALIDATION OK`，`DRY RUN ONLY: no database writes`。
- QA 已覆蓋：
  - DB payload/schema 草案。
  - Telegram summary-last / reply_markup-last。
  - 策略不變性。
  - 未來資料洩漏防線。
  - evidence failure 不阻斷報文。
  - external events 不接 BUY / `is_tradeable` / `action`。

## 明確未完成

- production schema apply。
- live Supabase write。
- live Telegram delivery。
- TWSE live replay / live backfill。
- 正式 backfill write。
- 真實外部新聞 / 題材 ingestion。
- Supabase RLS / 權限 / index / rollback 驗證。

以上都需 Owner 另開明確批准流程。

## 現有模組

- `main.py`：主要執行入口。
- `app.py`：Render 入口，觸發 GitHub Actions workflow。
- `core/watchlist.py`：12 檔股票唯一配置來源。
- `services/analysis.py`：策略決策來源。
- `core/generator.py`：報文產生、排序、Telegram 輸出。
- `core/condition_engine.py`：條件映射層。
- `services/stock_api.py`：行情與歷史資料來源。
- `services/signal_store.py`：`signal_runs / signal_items / signal_outcomes` 寫入。
- `services/daily_snapshot_store.py`：`daily_price / daily_signal_snapshot` 寫入。
- `core/signal_snapshot.py`：snapshot 組裝。
- `core/signal_validator.py`：snapshot 邏輯驗證。
- `services/position_store.py`：Supabase `positions` 持倉讀取。
- `services/strategy_evidence.py`：v20.0 策略證據資料層。
- `scripts/dry_run_replay.py`：dry-run replay。
- `scripts/backfill_signals.py`：受保護 backfill，預設不寫庫。
- `docs/v20_strategy_evidence_schema.sql`：v20.0 schema 草案。
- `supabase/functions/telegram-execution/index.ts`：Telegram 持倉文字命令處理。
- `tests/`：策略、formatter、snapshot、backfill/replay、行情來源與 evidence 測試。

## 已知風險

- `docs/v20_strategy_evidence_schema.sql` 尚未 production 套用。
- Evidence summary 依賴 DB 查詢；本地已驗證失敗降級，但 production latency 未測。
- `load_strategy_evidence_summary()` 查詢未顯式排序，後續可加 `.order("trade_date")`。
- backfill 正式寫庫會增加資料量，需 retention / archive 策略。
- 12 檔 watchlist 樣本偏小，策略證據第一版應維持 `樣本不足，不判讀`，避免過度解讀。
- `漏失` 一詞可能造成誤讀，後續可改成 `大漲漏失統計` 或補 `僅供檢討`。

## 流程狀態

- 固定 8 份 Markdown 工作流文件不得刪除，只允許更新內容：
  - `AGENTS.md`
  - `DISPATCH.md`
  - `RESEARCH.md`
  - `CURRENT_STATE.md`
  - `CLEANUP_PLAN.md`
  - `TASK.md`
  - `CHANGELOG.md`
  - `QA_REPORT.md`
- Architect 收到新功能 / 顯示 / bug / 策略需求時，預設只分派，不直接改代碼。
- Tech 自檢不等於 QA；QA 必須補直接消費者、跨區塊語意、使用者誤讀、負面案例與反證。
- production schema apply、live Supabase write、live Telegram delivery、正式 backfill write 都不是預設 QA L3，必須 Owner 明確批准。

## 影響模組判斷規則

- 報文分類、顯示文字、Telegram 卡片：`core/generator.py` 與 formatter tests。
- 持倉策略、買賣/續抱/停利/風控邏輯：`services/analysis.py` 與策略 tests。
- 行情來源、TWSE/Yahoo fallback、source 標示：`services/stock_api.py`、`core/generator.py` 與行情 tests。
- snapshot / DB 寫入保護：`services/daily_snapshot_store.py`、`services/signal_store.py`、`core/signal_validator.py`。
- replay/backfill：`scripts/dry_run_replay.py`、`scripts/backfill_signals.py` 與相關 tests。
- 策略證據資料層：`services/strategy_evidence.py`、`docs/v20_strategy_evidence_schema.sql`、replay/backfill tests。
- Telegram 持倉命令：`supabase/functions/telegram-execution/index.ts`。
