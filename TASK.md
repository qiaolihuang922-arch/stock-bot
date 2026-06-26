# TASK: future_watch_institutional_trading_20260626

## 任務狀態

- task_id: `future_watch_institutional_trading_20260626`
- 任務類型: `normal_patch`
- 狀態: `implemented_QA_pending_git`
- 版本建議: `v21.1`
- QA 分級: `L2`

## Owner 問題

Owner 指出三大法人買賣超不可能整批抓不到；前一版雖已移到 `關注標的財報`，但資料來源解析仍有錯誤，會讓部分市場或日期誤顯示 `資料不足`。

## 使用者可見結果

- 股票卡片仍不顯示三大法人行。
- `關注標的財報` 顯示昨日或最近可用交易日的三大法人買賣超。
- TWSE 日期若遇到假日、未發布或空資料，會回退查最近可用日期。
- TPEx 上櫃資料使用官方英文欄位解析，不再因欄位名不同而整批漏掉。

## 非目標

- 不發 live Telegram。
- 不寫 production DB。
- 不新增或變更 DB schema / RLS / grant / policy。
- 不改交易策略、持倉判斷或買賣決策。

## 影響模組與直接消費者

- `core/future_watch.py`: 三大法人 source 日期候選、TWSE/TPEx row parser、merge 規則。
- `tests/test_generator_report.py`: source regression 與 future-watch regression。
- 直接消費者: Telegram `【未來30日關注】` 的 `關注標的財報` 區塊。

## 輸出契約

- `關注標的財報` 每檔可顯示：
  - 股票代號與名稱。
  - EPS。
  - 營收 YoY。
  - `昨日三大法人買賣超 YYYYMMDD：外資 ...｜投信 ...｜自營 ...｜合計 ...`
- 缺資料只能在該財報區塊 fail closed 為 `昨日三大法人買賣超：資料不足`。
- 不得把缺資料輸出成 0。

## 版本契約

- 使用者可見版本維持 `v21.1`。
- 本輪修 source 與顯示資料完整性，不改策略版本。

## 驗收條件

- TWSE T86 今日空資料時會回退到最近可用交易日。
- TPEx OpenAPI 英文欄位可解析外資、投信、自營、合計與民國日期。
- live read-only probe 能同時合併 TWSE 與 TPEx institutional rows。
- focused future-watch regression 通過。

## 範例或 fixture

- TWSE fixture: `20260626` 空資料，`20260625` 有 2421 三大法人資料，最後顯示 `trade_date=20260625`。
- TPEx fixture: 6488 使用 `SecuritiesCompanyCode`、`TotalDifference`、`Date=1150625`。

## 失敗標本與驗收路由

- Owner correction: `不可能抓不到的 你一定是哪邊錯了`。
- 驗收路由: `build_live_stock_fundamentals_source` -> `collect_target_fundamentals` -> `format_future_watch_message`。

## 禁止事項與阻塞條件

- 不得只測 formatter 而不測 source row shape。
- 不得只查單一日 TWSE 後把空資料視為抓不到。
- 不得忽略 TPEx 官方英文欄位。
- 不得 live Telegram。
