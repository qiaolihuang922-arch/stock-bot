# TASK: future_watch_institutional_mobile_compact_20260626

## 任務狀態

- task_id: `future_watch_institutional_mobile_compact_20260626`
- 任務類型: `tiny_patch`
- 狀態: `implemented_QA_pending_git`
- 版本建議: `v21.1`
- QA 分級: `L1`

## Owner 問題

Owner 貼出盤後報文後指出 `關注標的財報` 的三大法人買賣超行太長；日期不需要顯示，只要表達「昨日」，並優化手機閱讀。

## 使用者可見結果

- 原格式：
  - `昨日三大法人買賣超 20260625：外資 +2,735.61張｜投信 -102張｜自營 -480.4張｜合計 +2,153.21張`
- 新格式：
  - `昨日三大法人：外+2,736｜投-102｜自-480｜合+2,153張`
- 不顯示日期。
- 小數張數取整。
- 單位 `張` 只在行尾顯示一次。
- 標籤縮短為 `外`、`投`、`自`、`合`。

## 非目標

- 不改資料來源。
- 不改策略判斷。
- 不改持倉 / 未持倉卡片。
- 不發 live Telegram。
- 不寫 DB。

## 影響模組與直接消費者

- `core/future_watch.py`: institutional trading display formatter。
- `tests/test_generator_report.py`: future-watch display regression。
- 直接消費者: Telegram `【未來30日關注】` 的 `關注標的財報` 區塊。

## 輸出契約

- `關注標的財報` 的法人行使用：
  - `昨日三大法人：外{n}｜投{n}｜自{n}｜合{n}張`
- 正數保留 `+`。
- 0 顯示為 `0`。
- 缺資料顯示 `昨日三大法人：資料不足`。

## 版本契約

- 使用者可見版本維持 `v21.1`。

## 驗收條件

- future-watch fixture 顯示短格式。
- 不再包含 `昨日三大法人買賣超 20260625`。
- 不再顯示小數張數如 `2,735.61張`。
- focused future-watch regression 通過。

## 範例或 fixture

- 2356 英業達:
  - raw: 外資 `2735.611`、投信 `-102`、自營 `-480.405`、合計 `2153.206`
  - output: `昨日三大法人：外+2,736｜投-102｜自-480｜合+2,153張`

## 失敗標本與驗收路由

- Owner specimen: 盤後 future-watch 報文中每檔法人行太長。
- 驗收路由: `format_future_watch_message` output。

## 禁止事項與阻塞條件

- 不得重新把日期塞回顯示行。
- 不得每個分項都重複 `張`。
- 不得保留小數張數。
