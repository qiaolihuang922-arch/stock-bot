# QA_REPORT.md

本文件由 QA 維護，提交給 Architect。只記錄本輪 v20.0 L3 驗證結果。

## 任務狀態

- 狀態：QA 驗證完成
- 對應任務：`v20.0-strategy-evidence-foundation`
- 版本：`v20.0`
- QA 等級：`L3`
- 提交日期：2026-05-26
- 依據文件：`AGENTS.md`、`DISPATCH.md`、`CURRENT_STATE.md`、`TASK.md`、`CHANGELOG.md`、`RESEARCH.md`

## 測試範圍

本輪依 `qa_level=L3` 驗證 v20.0 Strategy Evidence Foundation：

- full pytest。
- replay / backfill dry-run。
- DB payload / schema 草案。
- Telegram summary-last / reply_markup-last contract。
- 策略不變性：不得改 BUY / SELL、`is_tradeable`、`action`、RR / 過熱 / 停損 / 停利 / 加碼硬門檻。
- 未來資料洩漏：feature snapshot 不得含 future outcome，外部事件需 point-in-time 欄位。
- 證據層失敗不得阻斷既有 Telegram 報文。
- 外部資料不得直接影響 BUY / `is_tradeable` / `action`。

未執行 live Supabase write、live Telegram delivery、TWSE live replay/backfill。

## 執行命令

```bash
.venv/bin/python -m pytest
```

結果：

```text
99 passed, 21 warnings in 0.56s
```

```bash
.venv/bin/python scripts/dry_run_replay.py --dry-run --validate --source synthetic --version v20.0 --start-date 2026-05-18 --end-date 2026-05-22
```

結果：

```text
VALIDATION OK
STRATEGY EVIDENCE FEATURE ROWS: 60
```

```bash
.venv/bin/python scripts/backfill_signals.py --dry-run --source synthetic --version v20.0 --start-date 2026-05-18 --end-date 2026-05-22
```

結果：

```text
BACKFILL PLAN
daily_price rows: 60
daily_signal_snapshot rows: 60
market_daily_bars rows: 60
strategy_feature_snapshots rows: 60
strategy_outcome_metrics rows: 72
strategy_classification_audit rows: 0
VALIDATION OK
DRY RUN ONLY: no database writes
```

QA 補充 smoke：

```text
QA_SMOKE_OK 3 318 可買 可買
QA_DB_PAYLOAD_OK 12 12 0 36
```

## 測試結果

### Full Pytest

結果：通過。

- 共 99 項測試通過。
- 覆蓋既有 strategy、formatter、notifier、snapshot、validator、stock history、watchlist alignment 與新增 strategy evidence tests。
- 21 個 warnings 來自既有第三方套件 / Python 版本 deprecation，未指向本輪功能失敗。

### Replay / Backfill Dry-run

結果：通過。

- replay synthetic validate 通過。
- replay 產生 `STRATEGY EVIDENCE FEATURE ROWS: 60`。
- backfill dry-run 顯示新舊資料路徑 row count：
  - `daily_price rows: 60`
  - `daily_signal_snapshot rows: 60`
  - `market_daily_bars rows: 60`
  - `strategy_feature_snapshots rows: 60`
  - `strategy_outcome_metrics rows: 72`
  - `strategy_classification_audit rows: 0`
- backfill 明確輸出 `DRY RUN ONLY: no database writes`。

### DB Payload / Schema

結果：通過，schema 為草案可進 Architect 收口，但 production 套用前仍需 DBA / RLS / 權限確認。

已檢查：

- `docs/v20_strategy_evidence_schema.sql` 包含：
  - `market_daily_bars`
  - `strategy_feature_snapshots`
  - `strategy_outcome_metrics`
  - `strategy_classification_audit`
  - `market_events`
- 各主資料表有 primary key / unique key 以支援重跑冪等：
  - `market_daily_bars`: `(stock_id, trade_date, source)`
  - `strategy_feature_snapshots`: `(stock_id, trade_date, strategy_version)`
  - `strategy_outcome_metrics`: `(stock_id, trade_date, strategy_version, horizon_days)`
  - `strategy_classification_audit`: `(stock_id, trade_date, strategy_version, distortion_type)`
  - `market_events`: `dedupe_key unique`
- `market_events` 具備 point-in-time 欄位：`source_url`、`published_at`、`market_effective_at`、`ingested_at`。
- QA payload smoke 驗證收盤 12 檔可產生 12 筆 market rows、12 筆 feature rows；feature snapshot 不含 future outcome 欄位，outcome metrics 另行補算。

### Telegram Contract

結果：通過。

- `formatTelegramMessages()` 仍回傳多段 messages。
- `messages[-1]` 仍是總覽 summary。
- `📊 策略證據 v20.0` 併入最後 summary 段。
- `services.notifier.send_many()` mock 驗證 `reply_markup` 只綁最後 summary 段，前面詳情段不帶 `reply_markup`。
- 證據層錯誤摘要 `證據層略過：更新失敗 simulated` 出現在最後 summary 段，且既有 `🧭 今日結論`、`✅ 明日執行清單` 仍存在。

### 策略不變性

結果：通過。

- `git diff` 未顯示 `services/analysis.py`、`core/signal_snapshot.py`、`core/signal_validator.py`、`services/daily_snapshot_store.py`、`services/signal_store.py`、`services/notifier.py`、`services/stock_api.py`、`core/watchlist.py` 有本輪修改。
- 新增 evidence layer 只讀取 / 快照 `decision`、`action`、`is_tradeable`，沒有回寫策略結果。
- QA smoke 驗證原始 payload 的 `decision=BUY`、`action=0.1`、`is_tradeable=True` 在加入 evidence summary 後不變。
- `strategy_classification_audit` 只產生 audit row，不改 BUY / SELL / WAIT。

### 未來資料洩漏

結果：通過本輪可驗範圍。

- `strategy_feature_snapshots` payload 不含 `horizon_days`、`close_return_pct`、MFE、MAE、`outcome_label` 等 future outcome 欄位。
- `strategy_outcome_metrics` 與 feature snapshot 分表。
- outcome metrics 由 `calculate_outcome_metrics()` 另行使用未來 price rows 補算，不回填 feature generation。
- `market_events` schema 有 `published_at`、`market_effective_at`、`ingested_at`，但本輪僅為 schema 草案，未接入策略或績效計算。

### 外部資料不得直接影響 BUY / is_tradeable / action

結果：通過。

- 本輪沒有新聞 / 題材 / 法人 / 注意股 ingestion code。
- `market_events` 只存在於 schema 草案，未被 `services/strategy_evidence.py`、`core/generator.py`、`scripts/backfill_signals.py`、`scripts/dry_run_replay.py` 引用。
- 外部事件無路徑可直接改 `decision=BUY`、`is_tradeable=True` 或 `action`。

## 關聯風險掃描

直接呼叫方：

- `core/generator.generate_report()`：新增 evidence record / load，但包在 try/except；失敗時產生略過文字，不阻斷 messages。
- `core/generator.formatTelegramMessages()`：新增 `strategy_evidence_summary` 參數，預設 `None`，既有呼叫可相容。
- `services.notifier.send_many()`：未修改，contract smoke 通過。
- `scripts.dry_run_replay.py`：validate 時額外輸出 evidence feature rows，不改 validation 規則。
- `scripts.backfill_signals.py`：dry-run 顯示 evidence rows；正式寫庫仍需 `--write --confirm-write`。

下游與副作用：

- 正式 Supabase write 未執行。
- schema 尚未 production 套用，RLS / 權限 / index 實際效果未驗。
- 研究資料層沒有阻斷 Telegram path，但 production DB latency 尚未測。
- backfill evidence rows 會增加資料量，需 Architect 後續確認 retention / archive 策略。

## 跨區塊語意一致性

已檢查 Telegram summary 與 evidence summary 的語意：

- `📊 策略證據 v20.0` 是證據摘要，不覆蓋 `🧭 今日結論`。
- 樣本不足時顯示 `樣本不足，不判讀`，不產生買賣建議。
- evidence audit 用 `分類警示`，不是 `可買` 或 `必買`。
- 主交易區塊仍由既有策略決策控制；證據區塊只是事後績效 / audit 輔助。

結論：本輪未發現跨區塊語意把 evidence 誤包裝成交易指令。

## 使用者誤讀風險

已降低：

- 證據摘要標題為 `策略證據`，不是 `買點` 或 `推薦`。
- 低樣本顯示 `樣本不足，不判讀`。
- evidence failure 顯示 `證據層略過`，不會讓使用者誤以為策略失效。

殘留風險：

- `漏失` 一詞可能被解讀為策略錯誤而非事後統計；目前可接受，但 v20.1 若進一步面向使用者，可考慮改成 `大漲漏失統計` 或補充 `僅供檢討`。
- 第一版只看 12 檔 watchlist，分類績效樣本可能偏小；報文已用 `樣本不足，不判讀` 緩解。

## 質疑與反證

### PM 是否漏需求

未見關鍵漏需求。`TASK.md` 已包含 point-in-time、樣本不足、證據層失敗不阻斷報文、外部資料不得接 BUY 等硬邊界。

### Tech 是否漏同步

未見阻塞級漏同步。`CHANGELOG.md` 列出的新增檔案與實際 diff 一致；未影響模組中列出的策略核心與 notifier 未見 diff。

需 Architect 注意：`docs/v20_strategy_evidence_schema.sql` 是 schema 草案，尚不能視為 production DB 已完成。

### 測試是否能證明沒有破壞直接消費者

可以覆蓋本輪主要直接消費者：

- full pytest 通過。
- formatter-to-notifier smoke 通過。
- replay/backfill dry-run 通過。
- DB payload smoke 通過。

未覆蓋 live Telegram / live Supabase，因此 live delivery 與 production RLS 權限仍是殘留風險，不是本輪阻塞。

### QA 是否主動找到指定清單之外的風險

有。除指定清單外，QA 額外檢查：

- evidence failure summary 是否仍保留 `今日結論` 與 `明日執行清單`。
- feature snapshot 是否混入 future outcome 欄位。
- `market_events` 是否真的沒有被程式碼消費進 BUY 路徑。
- schema 草案是否有 point-in-time 與 idempotency key。
- `漏失` 文案可能帶來誤讀，但目前不構成 blocker。

## 驗收項結果

- `version_level=major`：通過。
- `qa_level=L3`：通過。
- full pytest：通過。
- replay dry-run：通過。
- backfill dry-run：通過。
- DB payload / schema 草案：通過，production 套用需另行核准。
- Telegram `messages[-1]` summary-last：通過。
- `reply_markup` last summary：通過。
- 策略不變性：通過。
- 未來資料洩漏防線：通過本輪可驗範圍。
- 證據層失敗不阻斷報文：通過。
- 外部資料不得直接影響 BUY / `is_tradeable` / `action`：通過。

## 未測項目

本輪未測：

- live Telegram delivery。
- live Supabase write。
- production schema apply / migration。
- Supabase RLS / 權限 / index performance。
- TWSE live replay / live backfill。
- 正式 backfill 寫庫。
- 真實外部新聞 / 題材 ingestion。

原因：

- `DISPATCH.md` / `TASK.md` 要求 L3 dry-run，不要求 live write。
- 正式 Supabase write、live Telegram delivery、production migration 依 `AGENTS.md` 需另行明確批准。
- `market_events` 本輪只交付 schema 草案，未交付 ingestion。

## 殘留風險

- Production DB schema 尚未套用，RLS / 權限 / index / migration rollback 未驗。
- Evidence summary 依賴 DB 查詢；本地已驗證失敗降級，但 production latency 未測。
- `load_strategy_evidence_summary()` 查詢未顯式排序，若 Supabase 回傳順序不穩，分類報告樣本窗口可能不完全可預期；目前不阻塞，但建議後續加 `.order("trade_date")`。
- backfill 正式寫庫會增加資料量；需 Architect 後續確認 retention / archive。
- 12 檔 watchlist 樣本偏小，策略證據第一版應維持 `樣本不足，不判讀` 防過度解讀。

## QA 結論

QA 結論：通過。

v20.0 Strategy Evidence Foundation 已通過 L3 驗證。full pytest、replay/backfill dry-run、DB payload/schema、Telegram contract、策略不變性、未來資料洩漏防線、證據層失敗降級與外部資料不接 BUY 路徑均未發現阻塞問題。

可交回 Architect 更新狀態；production schema apply、live Supabase write、live Telegram delivery 需另開明確批准流程。
