# CHANGELOG:

## 任務尺寸與風險

- 本輪 Re-Tech 尺寸：normal_patch。
- 原 TASK 為 minor / L3；本輪只修補既有 v20.4.45 第 4 則預設資料，不擴大產品方向、不改策略、不改 DB、不做 live delivery。

## 修改內容

- 在 `core.future_watch.default_future_watch_sources()` 補上 2026-06-04 起 30 日窗口的 global official event seed/snapshot。
- 預設全球事件不再是全域 `source-error`，會顯示官方 source 標記事件，formatter 仍只顯示最多 5 筆並保留日期區間 label。
- MOPS adapter 維持 fail-closed；歷史類比維持 insufficient-data / 低相似 fail-closed。
- 更新 `generate_report` focused test：預設第 4 則顯示 global events、保留候選、前三則不混入未來 30 日內容。

## 修改檔案

- `core/future_watch.py`
- `core/generator.py`
- `presentation/report.py`
- `tests/test_generator_report.py`

## 最小改動策略

- 只改 `default_future_watch_sources()` 的 global source 預設與對應測試。
- 未新增 live network adapter，未接 MOPS live request，未假造 MOPS / history。
- 未重構既有 formatter / generator message-list 組裝流程。

## 契約影響

- Public helper `default_future_watch_sources()` 的 `global_event_source` 預設由 `source-error` 改為 available official seed/snapshot。
- Message list 仍為可選第 4 則；既有第 1-3 則順序與 summary 決策語意不變。
- 第 4 則全球事件仍按日期升冪與 impact priority 排序，最多顯示 5 筆。
- 實際限制：global default 是 2026-06-04 這個 30 日窗口的官方 seed/snapshot；live official adapters、MOPS live adapter、historical analogy source 仍是 follow-up。

## 直接消費者同步

- `generate_report()` 透過既有 `default_future_watch_sources()` 消費新 global seed。
- `formatTelegramMessages()` / `render_telegram_messages()` 既有第 4 則接線維持。
- `tests/test_generator_report.py` 同步覆蓋 `generate_report` official message-list 層，不只測 helper。

## 未影響模組

- 未改買賣 / 加減碼 / 停損停利 / 持倉狀態機 / strategy decision。
- 未改 DB schema、RLS、grant、policy、role、index、constraint。
- 未做 production DB write、正式 backfill、live Telegram delivery。

## 已跑自檢命令

- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/v20_4_45_future_watch_seed_pytest arch -arm64 ./.venv/bin/python -m pytest tests/test_generator_report.py -k 'v20_4_45_future' -q` -> 3 passed。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/v20_4_45_future_watch_seed_wide arch -arm64 ./.venv/bin/python -m pytest tests/test_generator_report.py -k 'v20_4_45' -q` -> 4 passed。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/v20_4_45_future_watch_seed_pycompile arch -arm64 ./.venv/bin/python -m py_compile core/future_watch.py core/generator.py presentation/report.py tests/test_generator_report.py` -> passed。
- `git diff --check` -> passed。

## 覆蓋層級

- helper：global seed collection / date range / max 5 covered。
- formatter：future-watch message covered。
- official generator/message-list：`generate_report` default 第 4 則 covered。
- runner artifact / production source：未覆蓋。

## 殘留風險

- Global seed 是固定 snapshot；若官方日程改期，需要更新 seed 或接 live official adapter。
- MOPS 與 historical analogy 仍 fail-closed，尚未提供 live official data。
- 未跑 full pytest、production runner artifact、production DB source artifact、live Telegram。

## 旁支待辦

- 補 live official global event adapters。
- 補 MOPS official adapter 與跨月 production-safe replay artifact。
- 補 historical analogy official timeline source 與 similarity evidence artifact。
