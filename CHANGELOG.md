# CHANGELOG

## 2026-05-26 - v20.0 Strategy Evidence Foundation

### 修改內容
- 依 `TASK.md` 實作 v20.0 第一版策略證據基礎層。
- 新增策略證據資料層：
  - `market_daily_bars`：多日 OHLCV 研究資料。
  - `strategy_feature_snapshots`：策略當日特徵快照與穩定分類。
  - `strategy_outcome_metrics`：1 / 3 / 5 / 10 日 deterministic outcome metrics。
  - `strategy_classification_audit`：分類語意失真審計。
  - `market_events`：外部事件資料 schema 草案，只作研究資料，不接入買點。
- 新增 deterministic outcome 計算：
  - `close_return_pct`
  - `relative_return_pct`
  - `max_favorable_excursion_pct`
  - `max_adverse_excursion_pct`
  - `best_entry_gap_pct`
  - `outcome_label`
- 新增分類績效報告：
  - 覆蓋 `淘汰`、`等回測`、`RR不足`。
  - 報告顯示 3 日勝率與 5 日 MFE 中位數。
  - 樣本不足時顯示 `樣本不足，不判讀`，不硬判策略好壞。
- 新增分類審計：
  - 對高波動但被歸為弱勢 / 淘汰的案例產生審計 row。
  - 第一版用於捕捉「不追價合理但弱勢淘汰語意可能失真」類問題。
- Telegram summary 新增 `📊 策略證據 v20.0` 摘要區。
  - 若證據層寫入或查詢失敗，既有 Telegram 報文仍會發送。
  - 若樣本不足，顯示樣本不足，不改交易結論。
  - 保持 `messages[-1]` summary-last 與 reply_markup-last contract。
- replay / backfill dry-run 接入策略證據路徑：
  - replay validate 輸出 evidence feature row 數。
  - backfill dry-run 顯示 evidence table row 計畫。
  - 正式寫庫仍需既有 `--write --confirm-write`。
- 保留所有 BUY / SELL / RR / 過熱 / 停損 / 停利 / 加碼門檻不變。

### 修改檔案
- `core/generator.py`
- `services/strategy_evidence.py`
- `scripts/backfill_signals.py`
- `scripts/dry_run_replay.py`
- `docs/v20_strategy_evidence_schema.sql`
- `tests/test_strategy_evidence.py`
- `tests/test_generator_report.py`
- `tests/test_backfill_signals.py`
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
- Supabase Edge Function
- Telegram inline keyboard / `reply_markup` 產生邏輯
- 股票池
- 既有 snapshot guard
- 既有 daily_signal_snapshot / daily_price 寫入規則
- BUY / SELL / WAIT 決策門檻
- RR / 過熱 / 漲停不追 / 停損 / 停利 / 加碼硬門檻
- `decision / action / is_tradeable / is_best_candidate` 策略輸出

### 風險點
- `docs/v20_strategy_evidence_schema.sql` 是 schema 草案；正式套用 production 前需 DBA / QA 確認索引、RLS、權限與 upsert conflict key。
- `market_daily_bars` 在 synthetic dry-run 中若缺 open/high/low，證據層會用 close 做 fallback，以保證第一版 OHLCV row 完整；TWSE 真實 OHLCV 不受此 fallback 影響。
- 第一版分類 taxonomy 是穩定研究分類，不等於交易決策；QA 需確認使用者不會把 `策略證據` 誤讀成新的買賣指令。
- `strategy_classification_audit` 只產生審計資料，不會自動修正分類、買點或交易狀態。
- 外部事件表僅提供 schema，不接入新聞來源，也不會讓新聞直接產生 BUY / is_tradeable / action。
- 本次未跑 live Telegram、live Supabase write、TWSE live、正式 backfill 寫庫。
- 本次未跑 full pytest；依 Tech 任務範圍只跑 v20.0 相關局部測試、策略不變性 smoke、synthetic replay/backfill dry-run。

### 建議 QA 驗證範圍
- DB schema：
  - 確認 `market_daily_bars`、`strategy_feature_snapshots`、`strategy_outcome_metrics`、`strategy_classification_audit`、`market_events` 可在 Supabase 建表。
  - 確認 upsert conflict key 與 row idempotency。
- Evidence data layer：
  - 收盤 / 盤後完整 12 檔時可產生 feature rows。
  - 缺檔時 evidence path 應跳過，不污染每日樣本。
  - `market_daily_bars`、`strategy_feature_snapshots`、`strategy_outcome_metrics` row count 與預期一致。
- Outcome metrics：
  - 1 / 3 / 5 / 10 horizon 都有 deterministic outcome。
  - `relative_return_pct` 使用同日股票池平均作基準。
  - `MFE / MAE / best_entry_gap / outcome_label` 可重跑一致。
- Classification report：
  - `淘汰`、`等回測`、`RR不足` 樣本不足時不得判讀。
  - 樣本足夠時顯示 3 日勝率與 5 日 MFE 中位數。
  - 旺宏類高波動弱勢分類應產生 audit row，而不是直接改交易判斷。
- Telegram：
  - 總覽摘要最後一段包含 `📊 策略證據 v20.0`。
  - 證據層失敗時 Telegram 主報文仍能正常產生。
  - `messages[-1]` 仍是總覽摘要，reply_markup 仍綁最後一段。
- Strategy invariance：
  - 確認 BUY / SELL / WAIT 沒被 evidence layer 改動。
  - 確認 RR / 過熱 / 停損 / 停利 / 加碼門檻未放寬。
  - 確認外部事件表不會直接影響 BUY / is_tradeable / action。

### 已執行最低必要驗證
- `.venv/bin/python -m pytest tests/test_strategy_evidence.py tests/test_backfill_signals.py tests/test_generator_report.py`
  - 結果：`42 passed`
- `.venv/bin/python -m pytest tests/test_generator_report.py tests/test_dry_run_replay.py tests/test_notifier.py tests/test_daily_snapshot_store.py tests/test_signal_validator.py tests/test_analysis_engine.py`
  - 結果：`81 passed`
- `.venv/bin/python scripts/dry_run_replay.py --dry-run --validate --source synthetic --version v20.0 --start-date 2026-05-18 --end-date 2026-05-22`
  - 結果：`VALIDATION OK`
  - `STRATEGY EVIDENCE FEATURE ROWS: 60`
- `.venv/bin/python scripts/backfill_signals.py --dry-run --source synthetic --version v20.0 --start-date 2026-05-18 --end-date 2026-05-22`
  - 結果：`VALIDATION OK`
  - `daily_price rows: 60`
  - `daily_signal_snapshot rows: 60`
  - `market_daily_bars rows: 60`
  - `strategy_feature_snapshots rows: 60`
  - `strategy_outcome_metrics rows: 72`
  - `strategy_classification_audit rows: 0`
  - `DRY RUN ONLY: no database writes`

### 未執行測試
- full pytest：
  - 原因：本輪 Tech 任務要求局部實作與必要最小驗證，完整 QA / full regression 交由 QA 批次執行。
- TWSE live replay / live backfill：
  - 原因：避免外部資料源與網路波動干擾本輪局部驗證。
- Supabase production write：
  - 原因：本輪只交付 schema 草案與 dry-run path，不執行正式寫庫。
- Telegram live send：
  - 原因：formatter contract 已用 unit test 驗證，實際發送交 QA / staging 流程。
