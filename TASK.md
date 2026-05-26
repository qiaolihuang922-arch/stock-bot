# TASK: v20.0.1 Evidence Readiness Message

## 時間性

- 任務日期：2026-05-26
- 來源任務：`DISPATCH.md` Current Task / Current Result
- 目標版本：`v20.0.1`
- 任務性質：Telegram 策略證據區友善降級文案
- version_level：`patch`
- qa_level：`L2`
- 狀態：PM 正式需求，等待 Architect 交 Tech
- 邊界：只改 evidence readiness / friendly fallback / formatter 顯示與必要測試；不 apply production schema、不正式寫庫、不改策略、不改 BUY / SELL / `is_tradeable` / `action`。

## 需求目標

v20.0 已完成 Strategy Evidence Foundation，並在 Telegram 報文中新增 `📊 策略證據 v20.0`。

Owner 看到的 v20.0 盤後報文出現：

```text
證據層略過：更新失敗 {'message': "Could not find the table 'public.market_daily_bars' in the schema cache", ...}
```

這代表：

- evidence layer 降級有效，主報文沒有被阻斷。
- production schema 尚未 apply，Supabase 找不到 `market_daily_bars` 是已知狀態。
- 但 Telegram 不應直接露出 Supabase 原始 dict / error / schema cache 細節。

v20.0.1 目標是把 raw DB error 轉成 Owner 可理解的 readiness message，讓報文清楚表達：

```text
策略證據尚未啟用 / 資料表未建立 / 主報文不受影響
```

而不是把底層錯誤 dump 到 Telegram。

## 使用者可見變化

### 1. Schema 未啟用

當 production evidence schema 尚未建立，例如缺少 `market_daily_bars`、`strategy_feature_snapshots`、`strategy_outcome_metrics`、`strategy_classification_audit` 任一必要表時，Telegram 應顯示友善提示。

建議文案：

```text
📊 策略證據 v20.0
策略證據尚未啟用：資料表未建立，主報文不受影響
```

可接受等效文案：

```text
📊 策略證據 v20.0
證據層待啟用：production schema 尚未套用，主策略照常執行
```

不可出現：

```text
Could not find the table
schema cache
public.market_daily_bars
{'message': ...}
SupabaseException
Traceback
```

### 2. DB 查詢 / 寫入失敗

若 evidence layer 查詢或寫入失敗，但不是明確 schema missing，Telegram 應顯示可讀降級訊息。

建議文案：

```text
📊 策略證據 v20.0
證據層暫時略過：資料更新失敗，主報文不受影響
```

如需保留狀態，可顯示短碼，不顯示原始錯誤：

```text
📊 策略證據 v20.0
證據層暫時略過：DB_READ_FAILED，主報文不受影響
```

不可顯示：

- raw exception dict
- DB client stack trace
- SQL / schema cache 原文
- token / URL / key / connection detail

### 3. 樣本不足

當 evidence schema 已存在、查詢成功，但分類績效樣本不足時，應顯示樣本不足，而不是失敗。

建議文案：

```text
📊 策略證據 v20.0
樣本不足：需累積更多分類結果後啟用績效判讀
```

若有部分分類樣本不足：

```text
📊 策略證據 v20.0
淘汰｜樣本 3｜樣本不足，不判讀
等回測｜樣本 2｜樣本不足，不判讀
RR不足｜樣本 1｜樣本不足，不判讀
```

樣本不足不是錯誤，不應顯示為 `更新失敗`。

## 報文 / 流程設計

### Friendly Message Priority

證據區狀態應依下列優先級顯示：

```text
1. schema 未啟用 / evidence tables missing
2. DB 查詢或寫入失敗
3. 查詢成功但樣本不足
4. 查詢成功且樣本足夠，顯示分類績效摘要
```

### 報文範例

Schema 未啟用：

```text
📊 策略證據 v20.0
策略證據尚未啟用：資料表未建立，主報文不受影響
```

DB 暫時失敗：

```text
📊 策略證據 v20.0
證據層暫時略過：資料更新失敗，主報文不受影響
```

樣本不足：

```text
📊 策略證據 v20.0
樣本不足：需累積更多分類結果後啟用績效判讀
```

正常摘要仍維持 v20.0 格式：

```text
📊 策略證據 v20.0
淘汰｜樣本 42｜3日勝率 31%｜5日MFE中位 +1.2%
等回測｜樣本 28｜5日給更佳買點 46%
RR不足｜樣本 33｜3日相對 -0.8%
```

### 不改現有 Telegram 契約

本輪不得回退：

- 總覽摘要仍是 `messages[-1]`。
- `reply_markup` 仍綁在最後摘要段。
- evidence failure 不阻斷主報文。
- 策略證據區仍回到定時任務產生的 Telegram 報文。

## Edge Cases

- 多張 evidence 表缺失：只顯示一條友善啟用提示，不列出所有 raw table error。
- Supabase schema cache error：歸類為 schema 未啟用。
- 權限 / RLS / network / timeout：歸類為 DB 暫時失敗，不暴露 raw error。
- 查詢成功但無資料：顯示樣本不足。
- 部分分類有資料、部分不足：正常分類顯示結果，不足分類顯示 `樣本不足，不判讀`。
- evidence update 失敗但 summary load 成功：優先顯示可用 summary，可附短句 `本次更新略過`，不可顯示 raw error。
- evidence summary 產生失敗：顯示友善降級訊息，主報文仍正常。
- live schema 尚未 apply：不得引導 Owner 在 Telegram 內操作 schema；只提示另開啟用任務。
- 任何錯誤訊息不得包含 token、URL、完整 SQL、Supabase raw dict、Traceback。

## 影響模組初判

預期主要影響：

- `services/strategy_evidence.py`
  - evidence error classification
  - readiness / fallback message generation
  - schema missing vs DB failure vs insufficient sample 區分
- `core/generator.py`
  - Telegram evidence summary 顯示
- `tests/`
  - formatter / evidence fallback tests
  - strategy invariance smoke
  - Telegram contract tests

直接消費者需檢查：

- 定時任務入口
- `generate_report()`
- `formatTelegramMessages()`
- `main.py -> send_many()`
- `services/notifier.send_many()`

不預期影響：

- `services/analysis.py`
- BUY / SELL / `is_tradeable` / `action`
- `docs/v20_strategy_evidence_schema.sql`
- production schema
- live Supabase write
- replay/backfill 正式寫庫

## 不可變更範圍

本任務不可變更：

- 不 apply production schema。
- 不正式寫 Supabase。
- 不改 `docs/v20_strategy_evidence_schema.sql` 作為本輪必要項。
- 不改 BUY / SELL 判斷。
- 不改 `decision=BUY` 產生條件。
- 不改 `is_tradeable=True` 條件。
- 不改 `action_pct`。
- 不改 RR / 過熱 / 漲停不追 / 停損 / 停利 / 加碼門檻。
- 不把外部新聞 / 題材 / 法人 / 注意股接入買點。
- 不讓 evidence readiness failure 阻斷 Telegram 主報文。
- 不顯示 raw Supabase error、Traceback、schema cache dict、token、URL、key。

## 驗收標準

v20.0.1 需滿足：

1. `version_level` 為 `patch`。
2. `qa_level` 為 `L2`。
3. Schema 未啟用時，Telegram 顯示友善 readiness message。
4. Schema 未啟用時，Telegram 不顯示 `Could not find the table`。
5. Schema 未啟用時，Telegram 不顯示 `schema cache`。
6. Schema 未啟用時，Telegram 不顯示 raw dict，例如 `{'message': ...}`。
7. DB 查詢 / 寫入失敗時，Telegram 顯示友善降級訊息。
8. DB 查詢 / 寫入失敗時，主報文仍正常產生。
9. 樣本不足時，Telegram 顯示 `樣本不足` 或等效文案。
10. 樣本不足不得被顯示為 `更新失敗`。
11. 正常 evidence summary 格式不得回退。
12. `messages[-1]` summary-last contract 不得回退。
13. `reply_markup` last summary contract 不得回退。
14. 不改 BUY / SELL / `is_tradeable` / `action`。
15. 不 apply production schema、不正式寫庫。
16. 測試需覆蓋 schema missing、generic DB failure、insufficient sample 三種情境。
17. QA 需做 L2：formatter / evidence fallback、策略不變性、Telegram contract、直接消費者與使用者誤讀風險檢查。
