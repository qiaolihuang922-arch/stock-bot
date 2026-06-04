# QA_REPORT:

## 測試範圍

- 任務：`future_watch_query_interface_optimization_20260604`。
- 範圍：MOPS readonly 查詢參數、查詢預算、TYPEK 市場別優先、future-watch 第 4 則不回退。
- 未擴大到策略、DB、live Telegram。

## 關聯風險掃描

- `core/future_watch.py` 只改 readonly source collection，不含 DB client、upsert、delete 或 Telegram send。
- `core/generator.py` 未改，報文版本維持 `v20.4.47`。
- 手機可見報文不新增 diagnostics 噪音；query diagnostics 僅供測試與後續調校。

## 跨區塊語意一致性

- 第 4 則仍 append 在持倉 / 未持倉 / 決策簡報後。
- 第 4 則仍不使用 `可買`、`新倉建議`、`今日下單` 等交易語意。
- MOPS source-error 仍 fail closed，不會被顯示成無事件。

## 使用者誤讀風險

- 本輪不改可見版面，避免把技術查詢次數塞進手機報文。
- diagnostics 保留在 payload，後續若要顯示「查詢達上限」可另開顯示任務。

## 失敗標本反證

- 原風險：MOPS 以 `股票 × 月份 × TYPEK` 盲掃，股票多時接口會很久。
- 反證 1：focused budget test 強制 `max_targets=2`、`max_queries=3`，結果 `query_count=3` 且 `budget_exhausted=True`。
- 反證 2：上櫃股票 `exchange=上櫃` 首查 `TYPEK=otc`，查到 rows 後停止橫向掃描。
- 反證 3：read-only live smoke 光寶科 2301 已知上市時，MOPS `query_count=2`，仍列 06/05 / 06/22 法說會。

## 質疑與反證

- Focused future-watch tests：10 passed。
- py_compile：passed。
- `git diff --check`：passed。
- Read-only live smoke：
  - MOPS diagnostics：`query_count=2`、`target_count=1`、`budget_exhausted=False`。
  - 法說會內容：仍列光寶科 06/05 / 06/22。
  - 無 DB write、無 Telegram delivery。

## 未測項目

- 未跑 full `tests/test_generator_report.py -q`。
- 未跑 production runner artifact。
- 未做 live Telegram。
- 未做 DB read/write smoke。
- 未做全球事件 official calendar parser hardening。

## QA 結論

通過。

本輪查詢接口優化達成：MOPS 查詢有參數、有預算、有市場別優先與 early stop；第 4 則可見報文不回退，且 live smoke 仍能列真實法說會。
