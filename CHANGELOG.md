# CHANGELOG:

## 任務尺寸與風險

- 任務尺寸：tiny_patch。
- 風險：第 4 則 `歷史類比` 手機可見語意；不改策略、DB、live Telegram。

## 修改內容

- `core/future_watch.py`：
  - `CRASH_ANALOGY_FALLBACK` 改為 `無高相似台股急跌樣本`。
  - 歷史壓力模板事件改成台股口徑：
    - `2024/08/05 台股日圓套利平倉急殺`
    - `2020/03/12 台股疫情急跌`
    - `2015/08/20-24 台股急跌前段`
- `tests/test_generator_report.py`：
  - 更新 future-watch fixture 與 assertion。
  - 新增 `assertNotIn("全球股災", ...)` 防止報文字串回退。

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
- 歷史類比仍使用既有 TWSE 即時大盤 / 近月 OHLC features 與壓力模板。
- 使用者可見事件名稱改為台股市場語意，不再用全球股災作主事件。

## 直接消費者同步

- `format_future_watch_message()` 消費同一條 historical line。
- `generate_report()` / `generate()` append 的第 4 則同步吃到新字串。

## 未影響模組

- 未改 MOPS 查詢、法說會 formatter、EPS / 營收 source。
- 未改未來 30 日台股影響事件。
- 未改交易策略、RR、加減碼、停損停利、持倉狀態機。
- 未改 DB schema / write path / backfill / live Telegram。

## 自檢命令與結果

- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/v20_4_47_taiwan_analogy arch -arm64 ./.venv/bin/python -m pytest tests/test_generator_report.py -k 'v20_4_47_future or v20_4_47_live or v20_4_47_generate_report or mops_query' -q` -> 11 passed。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/v20_4_47_taiwan_analogy_pycompile arch -arm64 ./.venv/bin/python -m py_compile core/future_watch.py core/generator.py tests/test_generator_report.py` -> passed。
- `git diff --check` -> passed。
- Official `generate()` read-only smoke：第 4 則歷史類比顯示 `2015/08/20-24 台股急跌前段`，且 `CHECK_NO_GLOBAL_CRASH=True`。

## 覆蓋層級

- helper：TWSE pressure template expected text covered。
- formatter：future-watch message fixture covered。
- official generator：read-only smoke covered。

## 殘留風險

- 本輪只修語意模板；沒有新增多年台股股災歷史資料庫與相似度模型。
