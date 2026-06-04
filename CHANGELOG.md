# CHANGELOG:

## 任務尺寸與風險

- 任務尺寸：normal_patch。
- 風險：第 4 則 MOPS 法說會資訊密度與官方基本面資料讀取；不改交易策略、DB、live Telegram。

## 修改內容

- `core/future_watch.py`：
  - 新增 TWSE/TPEX 官方 OpenAPI 月營收與 EPS endpoints。
  - 新增 `build_live_stock_fundamentals_source()`，合併上市 / 上櫃最新月營收與最新季 EPS snapshot。
  - `collect_mops_events()` 將 fundamentals attach 到每筆法說會事件。
  - 法說會 event title 改用 MOPS `summary` / conference 名稱，並清理 `本公司受邀參加...說明...` 這類模板字。
  - 法說會 formatter 改為顯示 conference 名稱、EPS、營收YoY，不再顯示 `source=MOPS`。
  - `core/generator.py` 傳入 `fundamentals_source` 給 future-watch payload。
- `tests/test_generator_report.py`：
  - 更新 focused future-watch tests，反證法說會行顯示 conference 名稱、EPS 與營收YoY，且不再顯示 `source=MOPS`。

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
- 第 4 則 Telegram 版本維持 `v20.4.47`。
- 法說會行格式改為：`日期 代號 名稱｜conference｜EPS ...｜營收YoY ...｜關注原因：...`。
- 月營收採官方最新已公告月份；若當月未公告，OpenAPI snapshot 會自然落到上月或更早的最新公告月份。
- EPS 採官方最新季 EPS snapshot。

## 未影響模組

- 未改交易策略、RR、加減碼、停損停利、持倉狀態機。
- 未改 DB schema / RLS / grant / policy / write path。
- 未做 live Telegram delivery。
- 未改 GitHub workflow。
- 未改 MOPS 查詢窗口 / query order。
- 未改 global / TWSE 歷史類比查詢邏輯。

## 自檢命令與結果

- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/v20_4_47_mops_fund2 arch -arm64 ./.venv/bin/python -m pytest tests/test_generator_report.py -k 'v20_4_47_future or v20_4_47_live or v20_4_47_generate_report or mops_query' -q` -> 11 passed。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/v20_4_47_mops_fund2_pycompile arch -arm64 ./.venv/bin/python -m py_compile core/future_watch.py core/generator.py tests/test_generator_report.py` -> passed。
- `git diff --check` -> passed。
- Official `generate()` read-only smoke：法說會段顯示 conference 名稱、`EPS 2026Q1` 與 `營收YoY 2026/04`，例如光寶科 `Citi 2026 Taiwan Conference｜EPS 2026Q1 1.66｜營收YoY 2026/04 +24.5%`。

## 覆蓋層級

- helper：MOPS summary title cleanup and fundamentals merge covered。
- formatter：conference / EPS / revenue YoY visible line covered。
- official report message-list：focused `formatTelegramMessages` / `generate_report(dry_run=True)` retained。
- live smoke：official `generate()` read-only path covered；無 DB write、無 Telegram delivery。

## 殘留風險

- OpenAPI latest monthly revenue snapshot 在 2026-06-04 回傳 2026/04，代表 2026/05 尚未公告；這符合「當月沒有用上月 / 最新官方公告月」口徑。
- EPS 為最新季資料，不是月資料。
- Full `tests/test_generator_report.py -q` 仍有既有 legacy snapshot failures；本輪 focused future-watch 路徑通過。
