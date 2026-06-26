# QA_REPORT: future_watch_institutional_trading_20260626

## 測試範圍

- TWSE T86 空日回退。
- TPEx OpenAPI 英文 row shape。
- Future-watch `關注標的財報` 三大法人顯示。
- 股票卡片不顯示三大法人行。
- Read-only live source probe。

## 關聯風險掃描

- 原風險 1: TWSE 只查單一日期，假日或資料未發布時會誤判抓不到。
- 原風險 2: TPEx 官方 row 是英文欄位，舊 parser 沒吃到代號與買賣超欄位。
- 原風險 3: 後續日期 fallback 若覆蓋較新資料，會顯示舊交易日。
- 修正後: merge 先寫入者保留，候選日期依新到舊排列。

## 跨區塊語意一致性

- 三大法人買賣超只出現在 `關注標的財報`。
- 持倉/未持倉操作卡不混入財報/籌碼資料不足噪音。
- 缺資料只在財報區 fail closed，不輸出 0。

## 使用者誤讀風險

- 已降低：不再把官方空日或假日當成抓不到。
- 已降低：上櫃股票不再因英文欄位漏解析。
- 已降低：live probe 覆蓋 Owner 12 檔與 TPEx 樣本。

## 失敗標本反證

- Owner 指出 `不可能抓不到的`：
  - TWSE regression 反證 `20260626` 空資料會回退 `20260625`。
  - TPEx regression 反證英文欄位可解析。
  - live probe 反證 institutional rows 從 1326 擴到 2281，12 檔樣本皆有資料。

## 質疑與反證

- 質疑: 是否只是 fixture 可過？
  - 反證: read-only live probe 同時打官方 TWSE/TPEx endpoint。
- 質疑: 是否會用舊日期覆蓋新日期？
  - 反證: `_merge_institutional_rows` 已保留先寫入資料，候選日期從新到舊。
- 質疑: 是否發送或寫庫？
  - 反證: 本輪只跑 read-only source probe，未 live Telegram、未 DB write。

## 未測項目

- 未發 live Telegram。
- 未寫 production DB。
- 未跑 full suite；已知 full `tests/test_generator_report.py` 仍有舊文案預期清理項。

## QA 結論

conditional pass。

條件：source row shape 與 live read-only probe 已覆蓋本輪錯誤；full legacy suite 未清。
