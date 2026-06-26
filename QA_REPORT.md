# QA_REPORT: future_watch_fundamentals_spaced_layout_20260626

## 測試範圍

- Future-watch fundamentals final layout。
- Institutional line display regression。
- Read-only sample render。

## 關聯風險掃描

- 風險: 回到分行會變長。
  - 反證: Owner 明確指出兩行版太擠，分行較適合手機掃讀。
- 風險: 回退時移除法人判讀。
  - 反證: regression 保留 `昨日法人偏買/偏賣`。

## 跨區塊語意一致性

- Future-watch 財報區恢復卡片感。
- Summary、持倉卡、資料源修正不變。

## 使用者誤讀風險

- 已降低：每檔資料不再擠在同一行。
- 已降低：檔與檔中間有空行，手機掃讀較清楚。

## 失敗標本反證

- Owner specimen 的擠壓格式已改回：
  - 代號名稱 / EPS / 營收 / 法人 各自一行。

## 質疑與反證

- 質疑: 是否回退其他修正？
  - 反證: MOPS source-error 隱藏與法人判讀保留；source 未改。

## 未測項目

- 未發 live Telegram。
- 未寫 production DB。
- 未跑 full suite。

## QA 結論

通過。
