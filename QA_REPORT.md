# QA_REPORT: future_watch_institutional_trading_20260626

## 測試範圍

- 股票卡片負面檢查：不再顯示三大法人行。
- future-watch `關注標的財報` 顯示三大法人行。
- TWSE T86 官方資料 shape merge。
- Read-only live probe。

## 關聯風險掃描

- 原先每張卡顯示 `資料不足` 的噪音已移除。
- TWSE T86 盤中查今日可能空資料，已改查 `now - 1 day`。
- 官方股數欄位轉為 `張`，避免顯示過大股數。
- 缺資料仍 fail closed，不輸出 0。

## 跨區塊語意一致性

- 三大法人買賣超現在和 EPS / 營收同屬「關注標的財報」資訊。
- 持倉/未持倉操作卡不再混入財報/籌碼資料不足噪音。
- Future-watch 保留可追蹤資料，summary 不重複。

## 使用者誤讀風險

- 已降低：不再每檔卡片都看到 `抓不到資料`。
- 已降低：財報區有來源資料時直接顯示法人買賣超。
- 已降低：查詢昨日資料，避免盤中今日資料尚未生成而誤判為抓不到。

## 失敗標本反證

- Owner 指出「移動到關注標的財報」：
  - final card tests 反證卡片不含 `昨日三大法人買賣超`。
  - future-watch test 反證 `關注標的財報` 含 `昨日三大法人買賣超 20260625：...`。
- Owner 指出「現在顯示抓不到資料」：
  - live read-only probe 反證 TWSE source 可合併 1326 檔 institutional rows，2421 有資料。

## 質疑與反證

- 質疑: 是否只是把文字移到 future-watch，但資料仍抓不到？
  - 反證: live probe `INSTITUTIONAL_ITEMS=1326`, `HAS_2421` 有外資/投信/自營/合計。
- 質疑: 是否污染持倉/未持倉卡？
  - 反證: final card tests assert 不含三大法人行。
- 質疑: 是否發送或寫庫？
  - 反證: 本輪只跑 read-only source probe，未 live Telegram、未 DB write。

## 未測項目

- 未發 live Telegram。
- 未寫 production DB。
- 未跑 full suite；已知 full `tests/test_generator_report.py` 仍有舊文案預期清理項。
- TPEx live row shape 未單獨人工確認。

## QA 結論

conditional pass。

條件：TWSE live source 已確認可用；TPEx parser 具備基本兼容但需後續正式市場覆蓋驗證。
