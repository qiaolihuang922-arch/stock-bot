# TASK: future_watch_institutional_trading_20260626

## 任務狀態

- task_id: `future_watch_institutional_trading_20260626`
- 任務類型: `normal_patch`
- 狀態: `implemented_QA_conditional_pass_pushed`
- 版本建議: `v21.1`
- QA 分級: `L2`

## Owner 問題

Owner 要求把「昨日三大法人買賣超」從每張股票卡移到未來30日關注的 `關注標的財報` 區塊；同時指出目前顯示抓不到資料，需接上可用資料來源而不是只顯示 `資料不足`。

## 使用者可見結果

- 持倉卡與未持倉卡不再顯示 `昨日三大法人買賣超：資料不足`。
- `關注標的財報` 每檔股票在 EPS / 營收後顯示 `昨日三大法人買賣超`。
- TWSE 上市個股從官方 T86 三大法人日報抓昨日資料。
- TPEx 上櫃個股從 TPEx 三大法人 OpenAPI 嘗試抓取。
- 若官方來源仍不可用，僅在財報區 fail closed，不污染每張股票卡。

## 非目標

- 不發 live Telegram。
- 不寫 production DB。
- 不新增 DB schema / RLS / grant / policy。
- 不做跨日 backfill；本輪只做 read-only live source 與報文呈現。

## 影響模組與直接消費者

- `core/future_watch.py`: future-watch fundamentals source、institutional merge、format。
- `presentation/report.py`: 移除卡片層三大法人輸出。
- `tests/test_generator_report.py`: final card / future-watch regression。
- 直接消費者: Telegram `【未來30日關注】` 的 `關注標的財報` 區塊。

## 輸出契約

- 股票卡不得出現 `昨日三大法人買賣超`。
- `關注標的財報` 每檔可顯示：
  - 股票代號與名稱。
  - EPS。
  - 營收 YoY。
  - `昨日三大法人買賣超 YYYYMMDD：外資 ...｜投信 ...｜自營 ...｜合計 ...`
- TWSE T86 row 若為 `fields + data` 陣列，必須轉成 dict 後解析。
- 官方股數單位轉為 `張` 顯示。
- TWSE institutional 查詢日期使用 `now - 1 day`，避免盤中查今日自然空資料。

## 版本契約

- 使用者可見版本維持 `v21.1`。
- 本輪為報文區塊與 read-only source 修正，不改策略版本。

## 驗收條件

- final position/unheld cards 不含三大法人行。
- future-watch `關注標的財報` 顯示三大法人買賣超。
- live read-only probe 能從官方來源合併 institutional rows。
- focused future-watch regression 通過。

## 範例或 fixture

- 2421 建準，institutional payload:
  - 外資 `+1,200張`
  - 投信 `-300張`
  - 自營 `+50張`
  - 合計 `+950張`

## 失敗標本與驗收路由

- Owner correction: `買賣超移動到關注標的財報，而且現在顯示抓不到資料`。
- 驗收路由: `build_live_stock_fundamentals_source` -> `collect_target_fundamentals` -> `format_future_watch_message`。

## 禁止事項與阻塞條件

- 不得繼續在每張股票卡硬塞 `資料不足`。
- 不得把缺資料顯示成 0。
- 不得 live Telegram。
