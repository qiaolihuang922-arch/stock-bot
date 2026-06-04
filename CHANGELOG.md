# CHANGELOG:

## 任務尺寸與風險

- 任務尺寸：normal_patch。
- 風險：新增 live readonly source adapter，會影響第 4 則 `【未來30日關注】` 的資料來源與版本；不改策略 decision、持倉狀態機、DB read/write、live Telegram。
- runner_gap：Tech runner 兩次卡在互動層未產生 candidate diff；本輪由 Architect 依 PM TASK 做最小候選並送 QA，需在 QA / 收口記錄 runner_gap。

## 修改內容

- 將使用者可見版本升為 `v20.4.46`。
- `core/future_watch.py` 新增 live readonly source helpers：
  - TWSE OpenAPI 今日 / 近月 TAIEX source：成功讀取但歷史樣本不足時仍 fail closed，顯示 `source=TWSE`。
  - MOPS official POST adapter：能解析官方 table 才列法說會；遇 SPA shell / safety redirect / 無 table / 欄位不可辨識時回 `source-error`。
  - 全球事件 official live parser：嘗試讀 Fed / BLS / BOJ / BEA / ECB 官方頁；若全部解析失敗，保留固定 seed fallback 並標記 `seed-fallback`。
- `core/generator.py` 改為 `default_future_watch_sources(now)`，讓每次 `generate_report()` 依當次報文時間建立 live readonly sources。
- `tests/test_generator_report.py` 新增 v20.4.46 focused tests，覆蓋 TWSE source、MOPS blocked / parsed table、global live / fallback、official message-list 第 4 則與前三則不污染。

## 修改檔案

- `TASK.md`
- `CHANGELOG.md`
- `core/future_watch.py`
- `core/generator.py`
- `tests/test_generator_report.py`

## 最小改動策略

- 不改第 4 則既有區塊順序。
- 不改 `render_telegram_messages()` append 位置。
- 不新增依賴；沿用既有 `requests`。
- 不新增 DB source、cache、schema 或 write path。

## 契約影響

- `default_future_watch_sources()` 新增 optional `now` 參數，預設回傳 live readonly sources。
- 第 4 則歷史類比在 live TWSE insufficient 時會顯示 `｜source=TWSE`。
- MOPS source-error 不等於無事件；formatter 仍顯示 `法說會提醒：source-error（MOPS），本次不列事件`。
- 全球事件 source 可由 live official parser 或 seed fallback 提供；items 仍由 `collect_global_events()` 做 30 日窗口、日期排序、最多 5 筆。

## 直接消費者同步

- `generate_report()` 已傳入 `now` 給 `default_future_watch_sources(now)`。
- `formatTelegramMessages()` 既有 future watch source contract 保持可注入，測試可用 mock source 避免單元測試打外網。
- official message-list tests 覆蓋第 4 則 append 與前三則不污染。

## 未影響模組

- 未改交易策略、RR、加減碼、停損停利、持倉風控、can_buy/is_valid_entry。
- 未改 DB schema / RLS / grant / policy / role / index。
- 未做 DB read/write/backfill。
- 未做 live Telegram delivery。

## 已跑自檢命令

- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/v20_4_46_live_future_watch arch -arm64 ./.venv/bin/python -m pytest tests/test_generator_report.py -k 'v20_4_46_future or v20_4_46_live or v20_4_46_generate_report_appends_live' -q` -> 9 passed。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/v20_4_46_live_pycompile arch -arm64 ./.venv/bin/python -m py_compile core/future_watch.py core/generator.py presentation/report.py tests/test_generator_report.py` -> passed。
- `git diff --check` -> passed。
- Read-only live smoke：`build_future_watch_payload({}, 2026-06-04, **default_future_watch_sources(...))` -> 第 4 則輸出 TWSE insufficient + 5 筆全球事件；未送 Telegram、未寫 DB。

## 覆蓋層級

- helper：TWSE / MOPS / global live / fallback source helpers covered。
- formatter：第 4 則 source lines / fail-closed wording covered。
- official generator/message-list：`generate_report(dry_run=True)` append 第 4 則並保持前三則不污染 covered。
- production runner artifact：未覆蓋。

## 殘留風險

- MOPS official live 目前真實 probe 常回 SPA shell / safety page；本輪按 TASK fail closed，未硬解 SPA token。
- 全球官方頁 HTML 可能改版；全部 live parse 失敗時會回 seed fallback。
- 歷史崩盤類比仍保守：TWSE live source 可讀，但若歷史樣本不足或 similarity 不達標就 fail closed，不主觀硬套。
- 未跑 full pytest、production runner artifact、live Telegram。

## 旁支待辦

- 若 Owner 要法說會長期可用，需要另開 MOPS SPA/API reverse-engineering 或官方穩定 feed 任務。
- 若 Owner 要更完整歷史類比，需要補官方歷史 TAIEX 多年抓取與 deterministic similarity 規格。
- 補 runner_gap：Tech online runner 互動卡住時應有 noninteractive timeout / fallback。
