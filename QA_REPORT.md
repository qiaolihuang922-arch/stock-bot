# QA_REPORT: future_fundamentals_and_unheld_status_20260608

## 測試範圍
- focused report tests:
  - future 30-day message route。
  - afterhours denoise route。
  - message order / notifier route。
- `tests/test_market_theme_evidence.py` full file。
- official `generate_report(dry_run=True)` replay。

## 關聯風險掃描
- `關注標的財報` 使用同一批 watch/holding targets，不擴到全市場。
- 法說會 section 仍只列實際 MOPS events。
- 未持倉狀態文案只改顯示，不改 underlying funnel classification。

## 跨區塊語意一致性
- Summary 首行與詳情一致：
  - `未持倉 7（全部不可行動）`
  - `未持倉 7 檔全部不可行動`
- Future watch 分成三個語意區塊：
  - 法說會事件。
  - 關注標的財報。
  - 台股影響事件。
- 沒有法說會的關注股仍出現在財報區塊。

## 使用者誤讀風險
- 不再顯示 `漏斗（非執行）` 這種內部詞。
- 不再顯示 `僅追蹤0/淘汰7` 這種 0-count 流水。
- 財報區塊標題明確，不會被誤讀成法說會附屬資料。

## 失敗標本反證
- Owner 樣本 v20.4.50：
  - 財報資料只跟法說會出現 -> v20.4.51 改為每檔關注股財報。
  - `未持倉漏斗（非執行）：未持倉 7｜淘汰 7` -> v20.4.51 改為決策語句。
- official dry-run v20.4.51 confirmed。

## 未測項目
- live Telegram delivery 未測且禁止。
- 新年度營收 source 未新增；本輪沿用既有 official fundamentals source。

## QA 結論
通過
