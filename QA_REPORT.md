# QA_REPORT: afterhours_summary_trade_plan_v21_1_20260616

## 測試範圍

- 盤後 summary official message list。
- 今日買入 / 今日買入後風控 summary。
- 無新倉候選 / 可準備時的未持倉漏斗隱藏。
- 有可準備 / 新倉候選時仍保留必要狀態。
- Full regression suite。

## 關聯風險掃描

- 風險 1: 刪掉 summary 後失去明日行動。
  - 反證: dry-run summary 保留 `明日計畫`，列出持倉風控與未持倉分組追蹤。
- 風險 2: 今日買入紀錄被誤讀成有效新倉。
  - 反證: dry-run summary 顯示 `新倉無有效進場；今日買入紀錄已轉風控`。
- 風險 3: 可準備 / 新倉候選被隱藏。
  - 反證: targeted tests 保留 actionable / prepare 路徑的 summary 與 `未持倉狀態`。

## 跨區塊語意一致性

- Summary 與持倉卡一致：英業達、建準是減碼 / 停損優先。
- Summary 與未持倉卡一致：華邦電、南亞科等冷卻；旺宏、群創等回測；聯電等型態；仁寶、技嘉、緯創等接近。
- 無 `新增有效進場：無` 空占位，避免和 `明日計畫` 重複。

## 使用者誤讀風險

- 新 summary 以手機閱讀為主：
  - 先看結論。
  - 再看明日計畫。
  - 最後看持倉風控序列。
- 不再把統計數字包裝成決策。

## 失敗標本反證

- 原失敗: Owner 樣本中 summary 有市場統計、今日買入流水、未持倉漏斗，除持倉風控外資訊低價值。
- 反證 dry-run:
  - 無市場統計流水。
  - 無 `今日買入紀錄後風控` 重複行。
  - 無 `未持倉狀態` 漏斗。
  - 保留持倉風控檢查。

## 質疑與反證

- 質疑: 是否真的參考交易計畫規範？
  - 反證: 對照 Schwab / IG / ForTraders 後，summary 只保留 entry / risk / next action 類資訊。
- 質疑: 是否只硬刪文字？
  - 反證: actionable / prepare 時仍會顯示新倉候選或可準備資訊；不是無腦刪除。

## 未測項目

- 未做 live Telegram delivery。
- 未跑 GitHub runner artifact。
- 未做 DB write/backfill/prune。

## QA 結論

通過。
