# QA_REPORT:

## 測試範圍

- 任務：`future_watch_mops_fundamentals_context_20260604`。
- 範圍：future-watch 第 4 則法說會 conference 名稱、EPS、營收YoY、official `generate()` smoke。
- 未擴大到策略、DB、live Telegram。

## 關聯風險掃描

- `core/future_watch.py` 新增 readonly TWSE/TPEX OpenAPI financial snapshot 讀取，不含 DB client、upsert、delete 或 Telegram send。
- `core/generator.py` 只多傳 `fundamentals_source` 給 future-watch payload，未改交易決策。
- 報文版本維持 `v20.4.47`。

## 跨區塊語意一致性

- 第 4 則仍 append 在持倉 / 未持倉 / 決策簡報後。
- 第 4 則仍不使用 `可買`、`新倉建議`、`今日下單` 等交易語意。
- 法說會段仍只列未來 30 日 MOPS 事件。
- EPS / 營收 source-error 或缺欄位時不硬編數字。

## 使用者誤讀風險

- 同公司多場法說會原本都顯示 `法人說明會`，容易誤讀為重複；現在顯示 conference 名稱。
- EPS 與營收YoY 放在同一行，使用者不用再猜這場法說會對基本面關注點。
- 月營收採官方最新已公告月份；2026-06-04 official smoke 目前顯示 2026/04，代表 2026/05 尚未在 snapshot 中。

## 失敗標本反證

- 原風險：同檔股票多場法說會看起來像重複；Owner 要增加 EPS 與營收年增，當月沒有用上月。
- 反證 1：focused tests 檢查 MOPS summary conference 名稱可見。
- 反證 2：focused tests 檢查 EPS / 營收YoY 可見。
- 反證 3：focused tests 檢查不再顯示 `source=MOPS`。
- 反證 4：official `generate()` read-only smoke 顯示 2026Q1 EPS 與 2026/04 營收YoY。

## 質疑與反證

- Focused future-watch tests：11 passed。
- py_compile：passed。
- `git diff --check`：passed。
- Official `generate()` read-only smoke：
  - 光寶科：`Citi 2026 Taiwan Conference｜EPS 2026Q1 1.66｜營收YoY 2026/04 +24.5%`。
  - 聯電：`2026 Taiwan Tech Conference｜EPS 2026Q1 1.29｜營收YoY 2026/04 +10.8%`。
  - 英業達：`BofA 2026 Asia Conference｜EPS 2026Q1 0.68｜營收YoY 2026/04 +36.5%`。
  - 無 DB write、無 Telegram delivery。

## 未測項目

- 未跑 full `tests/test_generator_report.py -q`。
- 未跑 production runner artifact。
- 未做 live Telegram。
- 未做 DB read/write smoke。
- 未做 EPS QoQ / YoY 或完整年營收模型；本輪只顯示最新季 EPS 與最新官方月營收 YoY。
- 未做全球事件 official calendar parser hardening。

## QA 結論

通過。

本輪法說會資訊修正通過：同公司多場法說會可用 conference 名稱區分，並補最新季 EPS 與最新官方月營收 YoY。
