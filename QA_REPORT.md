# QA_REPORT: Holiday Execution Memory Fix

## 測試範圍

- 驗證 05/31 假日报文 execution memory、evidence 日期、strategy sample 分層。
- 不做 live Telegram、production write、schema change、backfill。

## 關聯風險掃描

- QA 第一輪阻塞：source ready 但 execution memory 缺 `sold_shares` 時仍可能輸出「第二段停利，本次建議 56 股」。
- Tech 第二輪已修：缺失或 zero memory 會 fail closed，不輸出賣出股數，不進明日計畫。

## 跨區塊語意一致性

- missing / zero execution memory：
  - action：`停利記憶不足`
  - 無「本次建議 56 股」
  - 無「明日風控｜第二段停利」
- 正常 `-112/-75` execution memory：
  - action：`第二段停利後觀察`
  - 顯示已執行不重複
  - 不進明日待賣計畫

## 使用者誤讀風險

- market/theme evidence 顯示 `latest_trade_date` / `lookback_range`，不只顯示 `same_trade_date`。
- `策略證據 v20.0` 標示為 strategy sample 層，不否定 market/theme production confirmed evidence。

## 質疑與反證

- QA 補了手機閱讀路徑反證：Summary、card、持倉風控、明日計畫不再互相矛盾。
- QA 補了 negative fixture：source ready + prior take-profit guard + missing/zero memory。

## 未測項目

- 未逐檔驗證所有股票的 historical execution memory。
- 未做 live Telegram。
- 未做 production DB write。

## QA 結論

通過
