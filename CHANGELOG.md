# CHANGELOG

## 2026-05-26 - v20.0.1 Evidence Readiness Message

### 修改內容
- 依 `TASK.md` 實作 v20.0.1 patch：策略證據區友善降級 / readiness message。
- `core/generator.py`
  - 報文版本升至 `v20.0.1`。
  - evidence summary 查詢失敗時，改把 exception 交給 evidence formatter 做分類與清洗。
  - evidence update 失敗時，不再把 `更新失敗 {raw exception}` 原樣塞入 Telegram。
  - 保持 evidence failure 不阻斷主報文。
- `services/strategy_evidence.py`
  - 新增 `strategy_evidence_error_kind()`。
  - 新增 `format_strategy_evidence_error()`。
  - schema / table missing 類錯誤顯示：
    - `策略證據尚未啟用：資料表未建立，主報文不受影響`
  - generic DB / network / timeout 類錯誤顯示：
    - `證據層暫時略過：資料更新失敗，主報文不受影響`
  - 不再輸出 raw Supabase dict、`Could not find the table`、`schema cache`、URL、token、Traceback 或連線細節。
- 測試補強：
  - schema missing error 會轉成 readiness message。
  - generic DB error 會轉成 sanitized fallback message。
  - 樣本不足仍維持樣本不足文案，不被誤判成更新失敗。
  - Telegram summary version contract 更新為 `v20.0.1`。

### 修改檔案
- `core/generator.py`
- `services/strategy_evidence.py`
- `tests/test_strategy_evidence.py`
- `tests/test_generator_report.py`
- `CHANGELOG.md`

### 未影響模組
- `services/analysis.py`
- `core/signal_snapshot.py`
- `core/signal_validator.py`
- `services/daily_snapshot_store.py`
- `services/signal_store.py`
- `services/position_store.py`
- `services/notifier.py`
- `services/stock_api.py`
- `services/ai.py`
- `services/learning.py`
- `core/watchlist.py`
- `scripts/dry_run_replay.py`
- `scripts/backfill_signals.py`
- `docs/v20_strategy_evidence_schema.sql`
- Supabase Edge Function
- production schema / DB migration
- live Supabase write
- live Telegram delivery
- replay / backfill 正式寫庫
- BUY / SELL / WAIT 決策門檻
- RR / 過熱 / 漲停不追 / 停損 / 停利 / 加碼硬門檻
- `decision / action / is_tradeable / is_best_candidate` 策略輸出

### 風險點
- schema missing 判斷依錯誤文字與 Supabase 常見 table-missing marker 分類；若 Supabase 未來更換錯誤格式，可能落到 generic DB fallback，但仍不會顯示 raw error。
- `📊 策略證據 v20.0` 標題維持 v20.0 evidence foundation 名稱；主報文版本已升為 `v20.0.1`。
- 本輪沒有 apply `docs/v20_strategy_evidence_schema.sql`，所以 production 若尚未建表，仍會顯示「策略證據尚未啟用」，這是預期 readiness 狀態。
- 本輪未改 evidence 寫入 / 查詢資料模型，只改錯誤分類與 Telegram 可讀文案。
- 本輪未跑 full pytest、live Telegram、live Supabase write、TWSE live、replay/backfill dry-run。

### 建議 QA 驗證範圍
- Evidence fallback：
  - schema 未建立時，Telegram evidence 區顯示 `策略證據尚未啟用：資料表未建立，主報文不受影響`。
  - schema 未建立時，不得顯示 `Could not find the table`。
  - schema 未建立時，不得顯示 `schema cache`。
  - schema 未建立時，不得顯示 raw dict，例如 `{'message': ...}`。
  - generic DB failure / timeout 時，顯示 `證據層暫時略過：資料更新失敗，主報文不受影響`。
- Telegram contract：
  - 主報文仍正常產生。
  - `messages[-1]` 仍是總覽摘要。
  - `reply_markup` 仍綁最後摘要段。
  - `📊 策略證據 v20.0` 區塊仍在 summary 中。
- Insufficient sample：
  - 查詢成功但無足夠樣本時，仍顯示 `樣本不足` 或各分類 `樣本不足，不判讀`。
  - 樣本不足不得被顯示為 `更新失敗`。
- Strategy invariance：
  - BUY / SELL / WAIT 不變。
  - `decision / action / is_tradeable / is_best_candidate` 不變。
  - RR / 過熱 / 漲停不追 / 停損 / 停利 / 加碼門檻不變。
- Direct consumers：
  - `generate_report()` 失敗降級路徑。
  - `formatTelegramMessages()` summary-last 輸出。
  - `services/notifier.send_many()` 對 messages list 的消費。

### 已執行最低必要驗證
- `.venv/bin/python -m pytest tests/test_strategy_evidence.py tests/test_generator_report.py tests/test_notifier.py`
  - 結果：`44 passed`
- `.venv/bin/python -m pytest tests/test_analysis_engine.py tests/test_signal_validator.py`
  - 結果：`33 passed`

### 未執行測試
- full pytest：
  - 原因：本輪為 patch，Tech 只做 L2 前置自檢；完整驗收交 QA。
- replay / backfill dry-run：
  - 原因：本輪未修改 replay/backfill 或 evidence row 計算，只改 Telegram readiness message。
- production schema apply：
  - 原因：`TASK.md` 明確禁止本輪 apply schema。
- live Supabase write：
  - 原因：`TASK.md` 明確禁止本輪正式寫庫。
- live Telegram delivery：
  - 原因：本輪以 formatter / notifier contract 測試驗證，實際 delivery 交 QA / staging 流程。
