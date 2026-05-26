# CURRENT_STATE.md

本文件由 Architect 維護，作為專案短上下文。新會話應先讀本文件，再依任務讀必要摘要文件或局部源碼。

## 專案狀態

- 專案：台股策略報文機器人。
- 目前穩定線：`v20.0.1 Evidence Readiness Message` 已完成、QA L2 通過並推送。
- 最新 commit：`2728a9e fix: hide raw strategy evidence errors`
- 交付形態維持不變：定時 GitHub Actions / 腳本 -> 產生 Telegram 報文 -> 發送給 Owner。
- 預設只處理 `core/watchlist.py` 的 12 檔股票。

## v20.0 已完成

- 新增 `services/strategy_evidence.py`：market bars、feature snapshots、outcome metrics、classification audit、classification report / Telegram evidence summary。
- 新增 `docs/v20_strategy_evidence_schema.sql` 作為 production schema 草案。
- `core/generator.py` 新增 `📊 策略證據 v20.0`。
- `scripts/dry_run_replay.py` 與 `scripts/backfill_signals.py` 接入 evidence dry-run path。
- QA L3 通過：full pytest `99 passed, 21 warnings`，synthetic replay/backfill dry-run 通過且不寫庫。

## v20.0.1 已完成

- 修正 evidence schema 未啟用時 Telegram 露出 Supabase raw error 的問題。
- schema missing 顯示：`策略證據尚未啟用：資料表未建立，主報文不受影響`。
- generic DB failure 顯示：`證據層暫時略過：資料更新失敗，主報文不受影響`。
- 樣本不足仍顯示樣本不足，不被誤判為更新失敗。
- 主報文版本升至 `v20.0.1`，策略證據區塊名稱仍為 `📊 策略證據 v20.0`。
- QA L2 通過：formatter / evidence fallback、notifier contract、策略不變性。
- 未 apply production schema、未正式寫庫、未改策略。

## 明確未完成

- production schema apply。
- live Supabase write。
- live Telegram delivery。
- TWSE live replay / live backfill。
- 正式 backfill write。
- 真實外部新聞 / 題材 ingestion。
- Supabase RLS / 權限 / index / rollback 驗證。

以上都需 Owner 另開明確批准流程。

## 目前進行中

- 無進行中任務；等待 Owner 下一個需求。

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
- `services/strategy_evidence.py`：v20.0 策略證據資料層與 v20.0.1 error fallback。
- `scripts/dry_run_replay.py`：dry-run replay。
- `scripts/backfill_signals.py`：受保護 backfill，預設不寫庫。
- `docs/v20_strategy_evidence_schema.sql`：v20.0 schema 草案。
- `supabase/functions/telegram-execution/index.ts`：Telegram 持倉文字命令處理。
- `tests/`：策略、formatter、snapshot、backfill/replay、行情來源與 evidence 測試。

## 已知風險

- `docs/v20_strategy_evidence_schema.sql` 尚未 production 套用。
- Production evidence schema 尚未 apply 前，Telegram 會顯示「策略證據尚未啟用」，這是預期狀態。
- Evidence summary 依賴 DB 查詢；本地已驗證失敗降級，但 production latency 未測。
- `load_strategy_evidence_summary()` 查詢未顯式排序，後續可加 `.order("trade_date")`。
- backfill 正式寫庫會增加資料量，需 retention / archive 策略。
- 12 檔 watchlist 樣本偏小，策略證據第一版應維持 `樣本不足，不判讀`，避免過度解讀。
- `漏失` 一詞可能造成誤讀，後續可改成 `大漲漏失統計` 或補 `僅供檢討`。

## 流程狀態

- 固定 8 份 Markdown 工作流文件不得刪除，只允許更新內容。
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
