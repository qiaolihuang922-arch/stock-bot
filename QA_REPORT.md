# QA_REPORT.md

## 任務狀態

- 對應任務：`v20.0-strategy-evidence-foundation`
- 版本：`v20.0`
- QA 等級：`L3`
- 提交日期：2026-05-26
- 結論：通過

## 測試範圍

- full pytest。
- replay / backfill dry-run。
- DB payload / schema 草案。
- Telegram summary-last / reply_markup-last contract。
- 策略不變性。
- 未來資料洩漏防線。
- 證據層失敗不阻斷既有 Telegram 報文。
- 外部資料不得直接影響 BUY / `is_tradeable` / `action`。

## 執行命令與結果

```bash
.venv/bin/python -m pytest
```

結果：`99 passed, 21 warnings`

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

## 驗證結論

- Full pytest：通過。
- Replay / backfill dry-run：通過，且 dry-run 不寫庫。
- DB payload / schema：通過本輪草案檢查；production 套用前仍需 RLS / 權限 / index / rollback 確認。
- Telegram contract：通過，`📊 策略證據 v20.0` 在最後 summary 段，`reply_markup` 綁最後段。
- 策略不變性：通過，未改 `services/analysis.py`，evidence layer 不回寫 BUY / SELL / WAIT。
- 未來資料洩漏：通過本輪可驗範圍，feature snapshot 與 outcome metrics 分表。
- 外部資料：通過，本輪僅有 `market_events` schema 草案，沒有 ingestion，也沒有接入交易決策。

## 關聯風險掃描

- `core/generator.generate_report()` 新增 evidence record/load，失敗會降級，不阻斷主報文。
- `core/generator.formatTelegramMessages()` 新增可選 `strategy_evidence_summary`，既有呼叫相容。
- `scripts.dry_run_replay.py` 只增加 evidence feature rows 輸出。
- `scripts.backfill_signals.py` dry-run 顯示 evidence rows；正式寫庫仍需 `--write --confirm-write`。

## 跨區塊語意一致性

- `策略證據` 沒有覆蓋 `今日結論` 或 `明日執行清單`。
- `樣本不足，不判讀` 不產生買賣建議。
- `分類警示` 不等同 `可買`、`必買`、`加碼` 或 `停損`。

## 使用者誤讀風險

- 已降低：證據摘要標題明確、低樣本不判讀、failure 顯示 `證據層略過`。
- 殘留：`漏失` 可能被理解為策略錯誤；後續可改為 `大漲漏失統計` 或補 `僅供檢討`。

## 未測項目

- live Telegram delivery。
- live Supabase write。
- production schema apply / migration。
- Supabase RLS / 權限 / index performance。
- TWSE live replay / live backfill。
- 正式 backfill 寫庫。
- 真實外部新聞 / 題材 ingestion。

## QA 結論

通過。v20.0 Strategy Evidence Foundation 可交 Architect 收口。production schema apply、live Supabase write、live Telegram delivery 需另開明確批准流程。
