# TASK: future_watch_taiwan_crash_analogy_20260604

## 任務狀態

- task_id：`future_watch_taiwan_crash_analogy_20260604`
- 任務類型：tiny_patch
- 狀態：done
- 版本建議：維持 `v20.4.47`
- QA 分級：L1

## Owner 問題

Owner 指出歷史類比不需要用全球股災模型；未來 30 日關注裡的歷史類比只要做台灣股災 / 台股急跌時間線。全球股災口徑可能不準、參考性不足。

## 使用者可見結果

- `歷史類比` 顯示的壓力模板改為台股口徑。
- 不再顯示 `2015/08/20-24 全球股災前段`。
- fallback 改為 `無高相似台股急跌樣本`，避免資料不足時仍像在找泛全球崩盤。

## 非目標

- 不改歷史類比資料來源與演算法。
- 不建立多年歷史資料庫。
- 不改 MOPS、EPS、營收、台股影響事件查詢。
- 不改策略、RR、持倉風控、買賣決策。
- 不改 DB schema/write/backfill，不發 live Telegram。

## 影響模組與直接消費者

- `core/future_watch.py`
- `tests/test_generator_report.py`
- Telegram 第 4 則 `【未來30日關注】`

## 輸出契約

- 台股壓力模板事件：
  - `2024/08/05 台股日圓套利平倉急殺`
  - `2020/03/12 台股疫情急跌`
  - `2015/08/20-24 台股急跌前段`
- 無高相似樣本時：`歷史類比：無高相似台股急跌樣本｜依據不足/相似度低`。
- 第 4 則報文不得出現 `全球股災`。

## 版本契約

- 使用者可見報文版本維持 `v20.4.47`，本輪只修正第 4 則歷史類比語意。

## 驗收條件

- Focused future-watch tests 通過。
- py_compile 通過。
- `git diff --check` 通過。
- Official `generate()` read-only smoke 的第 4 則歷史類比不得出現 `全球股災`，若有壓力類比應顯示台股口徑。

## 失敗標本與驗收路由

- 失敗標本：Owner 指出 `全球股災` 參考性不足，歷史類比應只做台灣股災 / 台股急跌。
- 驗收路由：TWSE historical source helper -> future-watch formatter -> official `generate()` read-only smoke。

## 禁止事項與阻塞條件

- 不得把全球事件或全球股災當作台股歷史類比主事件。
- 不得宣稱已完成多年歷史相似度模型；目前仍是 TWSE 即時 / 近月資料加壓力模板。
