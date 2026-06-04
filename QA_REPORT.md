# QA_REPORT:

## 測試範圍

- 任務：`future_watch_complete_v20_4_47`。
- 範圍：Telegram 第 4 則 future-watch 完成版、TWSE/MOPS/global source helper、focused official message-list。
- 未擴大到策略、DB、live Telegram。

## 風險預算與停止條件

- 風險 1：歷史類比像崩盤預測。驗證：輸出包含差異與關注條件，且 focused tests 禁止 `即將崩盤` / `重演`。
- 風險 2：MOPS 仍 source-error 或假造事件。驗證：live smoke 用 2301 查到真實 MOPS 06/05 / 06/22 法說會；malformed table 仍 source-error。
- 風險 3：全球事件 raw / 英文 / source= 技術欄位殘留。驗證：focused tests 檢查中文事件與 `來源：...官方/備援`。

## 關聯風險掃描

- `core/future_watch.py` 只新增 readonly HTTP parsing / formatting；未見 DB write 或 Telegram send。
- `core/generator.py` 僅版本升 `v20.4.47`。
- MOPS 多 TYPEK 查詢若其中一個市場 source-error，不會覆蓋其他市場已查到的事件。

## 跨區塊語意一致性

- 第 4 則仍 append 在持倉 / 未持倉 / 決策簡報後。
- 第 4 則仍不使用 `可買`、`新倉建議`、`今日下單` 等交易語意。
- 歷史類比標示 `差異：屬壓力前段，不是崩盤等級`，與非預測口徑一致。

## 使用者誤讀風險

- v20.4.47 live smoke 輸出比 v20.4.46 更可讀：
  - 歷史類比有具體情境：`2015/08/20-24 全球股災前段`。
  - MOPS 不再 source-error，列出 2301 光寶科 06/05 / 06/22 法說會。
  - 全球事件中文化，來源標 `備援`。
- 殘留：全球事件目前 live parser 在 smoke 中走備援，後續若要全官方即時可另開 parser hardening。

## 質疑與反證

- Focused future-watch tests：9 passed。
- py_compile：passed。
- `git diff --check`：passed。
- Read-only live smoke：
  - TWSE：輸出壓力情境與相似點。
  - MOPS：`adapter` 回 2301 三筆法說會，其中 06/05、06/22 落在未來 30 日並顯示。
  - Global：中文事件、`來源：...備援`。
- Full `tests/test_generator_report.py -q`：30 failed / 152 passed；failures 為既有未持倉漏斗 / legacy snapshot，未作為本輪 completion gate。

## 未測項目

- 未跑 production runner artifact。
- 未做 live Telegram。
- 未做 DB read/write smoke。
- 未把全球事件 live parser 改成完整 calendar feed parser。
- 未做 TWSE 多年 deterministic similarity 統計模型。

## QA 結論

conditional pass。

本輪 Owner 指出的第 4 則完成版問題已修：TWSE 有壓力情境、MOPS 能列真實法說會、全球事件中文化。conditional 原因是全量 `tests/test_generator_report.py` 仍有舊 snapshot failures，與本輪 future-watch 路徑無直接關聯。
