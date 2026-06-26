# TASK: future_watch_fundamentals_spaced_layout_20260626

## 任務狀態

- task_id: `future_watch_fundamentals_spaced_layout_20260626`
- 任務類型: `tiny_patch`
- 狀態: `implemented_QA_passed_pushed`
- 版本建議: `v21.1`
- QA 分級: `L1`

## Owner 問題

Owner 指出 `關注標的財報` 兩行壓縮版太擠，要改回之前較好掃的分行版本。

## 使用者可見結果

- 財報區每檔恢復：
  - 代號名稱一行。
  - EPS 一行。
  - 營收一行。
  - 昨日法人一行。
  - 檔與檔中間留空行。
- 保留既有改善：
  - MOPS source-error 不顯示。
  - 法人偏買/偏賣判讀保留。
  - 資料源修正保留。

## 非目標

- 不改資料來源。
- 不改 summary 明日優先。
- 不改策略與 DB。
- 不發 live Telegram。

## 影響模組與直接消費者

- `core/future_watch.py`: future-watch fundamentals layout。
- `tests/test_generator_report.py`: layout regression。
- 直接消費者: Telegram `【未來30日關注】` 的 `關注標的財報` 區塊。

## 輸出契約

- 不使用 `2356 英業達｜EPS...｜營收...` 的擠壓單行格式。
- 使用分行格式：
  - `2356 英業達`
  - `EPS 2026Q1 0.68`
  - `營收 2026/05 +35.3%`
  - `昨日法人偏買：...`

## 版本契約

- 使用者可見版本維持 `v21.1`。

## 驗收條件

- future-watch / institutional focused regression 通過。
- sample render 顯示分行格式與空行。

## 範例或 fixture

- 2356、2376、2421 sample render。

## 失敗標本與驗收路由

- Owner specimen: 兩行壓縮財報區太擠。
- 驗收路由: `format_future_watch_message` final output。

## 禁止事項與阻塞條件

- 不得回到擠壓單行格式。
- 不得移除法人判讀。
