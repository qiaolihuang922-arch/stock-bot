# TASK: future_watch_taiwan_crash_template_library_20260604

## 任務狀態

- task_id：`future_watch_taiwan_crash_template_library_20260604`
- 任務類型：normal_patch
- 狀態：done
- 版本建議：維持 `v20.4.47`
- QA 分級：L2

## Owner 問題

Owner 認為歷史類比模板太少，要求把台股歷史股災模板都加入並做分析。現況只有三段壓力模板，容易讓第 4 則歷史類比看起來樣本不足、判斷過粗。

## 使用者可見結果

- `歷史類比` 改由台股歷史急跌樣本庫挑選最相近事件。
- 報文顯示樣本庫件數，讓使用者知道不是只靠三個模板。
- 仍只顯示最相近的一條類比，保持手機可讀。
- 不把歷史類比寫成預測或交易指令。

## 非目標

- 不建立 DB 或多年 OHLC 歷史資料表。
- 不改 TWSE live source 讀取方式。
- 不改 MOPS、EPS、營收、台股影響事件。
- 不改策略、RR、持倉風控、買賣決策。
- 不發 live Telegram。

## 影響模組與直接消費者

- `core/future_watch.py`
- `tests/test_generator_report.py`
- Telegram 第 4 則 `【未來30日關注】`

## 輸出契約

- 新增台股歷史急跌樣本庫，至少包含：
  - 1990 台股萬點泡沫崩跌
  - 1995 台海飛彈危機
  - 1997 亞洲金融風暴
  - 2000 網路泡沫 / 政權輪替壓力
  - 2003 SARS 急跌
  - 2004 319 選舉事件急跌
  - 2008 金融海嘯
  - 2011 歐債 / 美國信評急跌
  - 2015 台股急跌 / 中國股災外溢
  - 2018 美股波動 / 貿易戰急跌
  - 2020 台股疫情急跌
  - 2022 升息通膨修正
  - 2024 台股日圓套利平倉急殺
- 顯示格式保留單行：`歷史類比：事件｜相似度 ...｜相似：...｜差異：...｜關注：...｜樣本庫 台股歷史急跌 N件｜source=TWSE`。

## 版本契約

- 使用者可見報文版本維持 `v20.4.47`。

## 驗收條件

- Focused future-watch tests 通過。
- py_compile 通過。
- `git diff --check` 通過。
- Official `generate()` read-only smoke 第 4 則需顯示 `樣本庫 台股歷史急跌`，且不得出現 `全球股災`。

## 失敗標本與驗收路由

- 失敗標本：Owner 指出模板太少，要求加入台股歷史股災模板做分析。
- 驗收路由：台股樣本庫 helper -> TWSE pressure source -> future-watch formatter -> official `generate()` read-only smoke。

## 禁止事項與阻塞條件

- 不得把全球事件當成歷史類比主樣本。
- 不得宣稱已完成多年統計模型；本輪是 deterministic template library + live TWSE features。
