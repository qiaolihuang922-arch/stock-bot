# QA_REPORT: explicit_approach_zone_wording_v21_1_20260616

## 測試範圍

- 未持倉 `等接近` 卡片。
- 遠離突破但不淘汰的 regression。
- Official dry-run 技嘉卡片。
- Full regression suite。

## 關聯風險掃描

- 風險 1: 文案變清楚但策略被改動。
  - 反證: 只改 `presentation/report.py` formatter；`core/generator.py` 未改。
- 風險 2: 無突破區欄位時報文空白。
  - 反證: fixture 無 `retest_zone_low/high` 時 fallback 為 `突破區/回測支撐`。
- 風險 3: 可買語氣誤導。
  - 反證: 仍顯示 `進場：不買`，可買只列條件。

## 跨區塊語意一致性

- `距突破` 保留。
- `進場` / `缺口` / `可買` / `明日觸發` 都指向同一個突破區。
- 技嘉仍是 `等接近｜遠離觸發`，沒有升格可買。

## 使用者誤讀風險

- 低於舊版：不再需要猜 `買點區` 是哪個區。
- 新文案明確表示還差的是接近 `突破區 399~400.99`。

## 失敗標本反證

- 原失敗: 技嘉顯示 `還沒到買點區`。
- 反證: dry-run 技嘉顯示 `尚未接近突破區 399~400.99`。

## 質疑與反證

- 質疑: 是否硬改文字？
  - 反證: 文案從 payload 的 `retest_zone_low/high` 取值；無欄位才 fallback。

## 未測項目

- 未做 live Telegram delivery。
- 未跑 GitHub runner artifact。
- 未做 DB write/backfill/prune。

## QA 結論

通過。
