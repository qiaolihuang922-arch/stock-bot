# CHANGELOG:

## 任務尺寸與風險

- 任務尺寸：normal_patch。
- 風險：第 4 則 `歷史類比` 樣本庫與相似度選擇；不改策略、DB、live Telegram。

## 修改內容

- `core/future_watch.py`：
  - 新增 `TAIWAN_CRASH_TEMPLATE_LIBRARY`，共 13 件台股歷史急跌 / 股災模板。
  - 模板包含事件名稱、單日跌幅區間、高檔回落區間、基礎相似度、差異說明與後續關注條件。
  - 新增 `_band_similarity()` / `_score_taiwan_crash_template()`，用 TWSE live features 對樣本庫做 deterministic scoring。
  - `_historical_pressure_template()` 改為從樣本庫挑最高分模板；低於門檻才落一般高檔震盪回測。
  - `_build_twse_pressure_line()` 顯示 `樣本庫 台股歷史急跌 13件`。
- `tests/test_generator_report.py`：
  - 更新 06/04 壓力樣本 expectation：`2015 台股急跌/中國股災外溢`、相似度 67%、樣本庫 13 件。
  - 新增 2024/08/05 -8.35% 急殺案例，反證 severe day 會配到 `2024/08/05 台股日圓套利平倉急殺`。
  - 保留 `全球股災` 不得出現在 final future-watch 的反證。

## 修改檔案

- `core/future_watch.py`
- `tests/test_generator_report.py`
- `TASK.md`
- `CHANGELOG.md`
- `QA_REPORT.md`
- `DISPATCH.md`
- `CURRENT_STATE.md`
- `CLEANUP_PLAN.md`

## 契約影響

- 第 4 則 Telegram 版本維持 `v20.4.47`。
- 歷史類比仍使用 TWSE 即時大盤 / 近月 OHLC features。
- 相似事件不再是三段硬判斷，而是台股 13 件樣本庫 scoring。
- 顯示格式新增 `樣本庫 台股歷史急跌 13件`。

## 直接消費者同步

- `format_future_watch_message()` 消費同一條 historical line。
- `generate_report()` / `generate()` append 的第 4 則同步顯示樣本庫與最佳相似事件。

## 未影響模組

- 不改交易策略、RR、加減碼、停損停利、持倉狀態機。
- 不改 DB schema / write path / backfill / live Telegram。

## 自檢命令與結果

- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/v20_4_47_crash_library arch -arm64 ./.venv/bin/python -m pytest tests/test_generator_report.py -k 'v20_4_47_future or v20_4_47_live or v20_4_47_generate_report or mops_query' -q` -> 12 passed。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/v20_4_47_crash_library_pycompile arch -arm64 ./.venv/bin/python -m py_compile core/future_watch.py core/generator.py tests/test_generator_report.py` -> passed。
- `git diff --check` -> passed。
- Official `generate()` read-only smoke：第 4 則顯示 `2015 台股急跌/中國股災外溢｜相似度 67%｜...｜樣本庫 台股歷史急跌 13件｜source=TWSE`，且 `CHECK_LIBRARY=True`、`CHECK_NO_GLOBAL_CRASH=True`。

## 覆蓋層級

- helper：13 件 template library、mild pressure、severe 2024 template covered。
- formatter：future-watch final fixture covered。
- official generator：read-only `generate()` smoke covered。
- production source：TWSE / MOPS / fundamentals read-only smoke covered；無 DB write、無 live Telegram。

## 殘留風險

- 本輪仍不是多年 OHLC 統計相似度模型；是 deterministic template library + live TWSE features。
- 各歷史事件的區間是模板化分析用，不是精確回測資料表。
