# QA_REPORT: telegram_all_cards_institutional_trading_20260626

## 測試範圍

- 持倉 final card。
- 未持倉 final card。
- 三大法人資料缺失 fail closed。
- 三大法人資料存在時的外資/投信/自營/合計格式。
- 前一輪 Telegram readability focused regression。

## 關聯風險掃描

- 每檔股票都輸出，不限可買/買檔。
- 缺資料不輸出 0，避免誤導。
- formatter 支援多個 payload key，方便後續資料源接入。
- 新增行不改策略判斷與分組。

## 跨區塊語意一致性

- 持倉與未持倉卡片欄位一致。
- Summary 不重複塞法人行，避免手機簡報過重。
- 無資料時統一用 `資料不足`，不與既有 source-status 混淆。

## 使用者誤讀風險

- 已降低：每檔股票都會看到三大法人欄位，不會只出現在買檔。
- 已降低：缺資料時清楚標示，避免把缺資料看成法人沒有買賣超。

## 失敗標本反證

- Owner correction `是每一檔股票` 已用 final card 測試反證：
  - 持倉 card 含 `昨日三大法人買賣超：資料不足`
  - 未持倉 card 含 `昨日三大法人買賣超：資料不足`
  - 有資料 card 含 `外資 +1,200張｜投信 -300張｜自營 +50張｜合計 +950張`

## 質疑與反證

- 質疑: 是否只加到買檔？
  - 反證: 測試同時檢查持倉與未持倉非買檔 final card。
- 質疑: 缺資料是否會誤顯示 0？
  - 反證: 無資料 fixture 顯示 `資料不足`。
- 質疑: 是否破壞前一輪 readability 修復？
  - 反證: combined focused regression `6 passed, 229 deselected`。

## 未測項目

- 未發 live Telegram。
- 未讀寫 production DB。
- 未新增或驗證正式三大法人抓取源。
- 未跑 full suite；既有 full `tests/test_generator_report.py` 舊文案預期仍是清理項。

## QA 結論

conditional pass。

條件：所有股票卡片硬輸出三大法人買賣超欄位已由 final card tests 覆蓋；正式資料源接入另開任務。
