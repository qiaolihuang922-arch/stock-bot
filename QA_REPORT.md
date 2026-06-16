# QA_REPORT: rebound_retest_anchor_wording_v21_1_20260616

## 測試範圍

- 未持倉 `等回測｜反彈修復待回測` 卡片。
- DB-backed recent daily close source gate。
- Official dry-run 群創 / 旺宏卡片。

## 關聯風險掃描

- 風險 1: 只是硬改文字，策略仍可能假記憶。
  - 反證: `core/generator.py::persistent_recent_price_values` 必須 `cross_day_ready` 且 `source_of_truth` 包含 `daily_price`，才會回傳跨日收盤。
- 風險 2: 將最近收盤誤稱為支撐。
  - 反證: 報文改為 `最近反彈收盤`，測試禁止 `最近修復支撐`。
- 風險 3: 誤導成已可買。
  - 反證: card 仍顯示 `進場：不買，等回測`，可買只列條件。

## 跨區塊語意一致性

- 標題 `等回測`、進場 `不買，等回測`、缺口 `等待回測最近反彈收盤` 一致。
- `距突破` 保留，不作為本輪修改目標。
- Summary 未新增可買訊號。

## 使用者誤讀風險

- 舊版 `修復支撐` 容易被理解成已完成支撐識別。
- 新版明確表示只是最近反彈後的日收盤錨點，後續仍要等待回測不破。

## 失敗標本反證

- 原失敗: 群創顯示 `最近修復支撐 53.3`。
- 反證: dry-run 群創顯示 `最近反彈收盤 53.3`。

## 質疑與反證

- 質疑: 「等回測」是不是假的？
  - 反證: 不是 agent memory；來源是 Supabase `daily_price` 經 `services/cross_day_context.py` 載入的 `recent_daily_price_points`。缺 source 時會清空 recent points，策略不會升格成 multi-day rebound。
- 質疑: 系統如何知道已回測？
  - 反證: 現在不是說已回測；它只說等待回測。下一次日線 / 即時價回到最近反彈收盤附近且不破，才可重新評估。

## 未測項目

- 未做 live Telegram delivery。
- 未做 DB write/backfill/prune。
- 未跑 GitHub runner artifact。

## QA 結論

通過。
