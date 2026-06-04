# CHANGELOG:

## 任務尺寸與風險

- 任務尺寸：tiny_patch。
- 風險：第 4 則手機可見語意；不改資料查詢、交易策略、DB、live Telegram。

## 修改內容

- `core/future_watch.py`：
  - 第 4 則 MOPS 段標題由 `法說會提醒` 改為 `未來30日法說會`。
  - 第 4 則事件段標題由 `全球事件` 改為 `未來30日台股影響事件`。
  - source-error / empty 文案同步使用新語意，避免錯誤時回退到舊標題。
- `tests/test_generator_report.py`：
  - 更新 focused future-watch tests，反證前三則不污染、第 4 則新標題排序正確、舊 `全球事件` / `法說會提醒` 標題不再出現。

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
- 可見段落改為 `歷史類比`、`未來30日法說會`、`未來30日台股影響事件`。
- 法說會與台股影響事件明確限定未來 30 日；歷史類比不受此標題限定。

## 未影響模組

- 未改交易策略、RR、加減碼、停損停利、持倉狀態機。
- 未改 DB schema / RLS / grant / policy / write path。
- 未做 live Telegram delivery。
- 未改 GitHub workflow。
- 未改 MOPS / global / TWSE 查詢邏輯。

## 自檢命令與結果

- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/v20_4_47_taiwan_event_labels arch -arm64 ./.venv/bin/python -m pytest tests/test_generator_report.py -k 'v20_4_47_future or v20_4_47_live or v20_4_47_generate_report or mops_query' -q` -> 10 passed。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/v20_4_47_taiwan_event_labels_pycompile arch -arm64 ./.venv/bin/python -m py_compile core/future_watch.py core/generator.py tests/test_generator_report.py` -> passed。
- `git diff --check` -> passed。
- Read-only live smoke with 光寶科 2301：第 4 則顯示 `未來30日法說會` 與 `未來30日台股影響事件`，仍顯示 06/05 / 06/22 法說會。

## 覆蓋層級

- helper：既有 future-watch source path retained。
- formatter：新段落標題與 source-error 文案 covered。
- official report message-list：focused `formatTelegramMessages` / `generate_report(dry_run=True)` retained。
- live smoke：read-only MOPS official path covered；無 DB write、無 Telegram delivery。

## 殘留風險

- 全球事件 official parser 仍可能 fallback seed；本輪只處理可見語意，不做全球 calendar hardening。
- `影響台股` 目前是顯示語意與種子事件選集，不是新增事件影響評分模型；後續若要更精準可新增台股影響分級。
- Full `tests/test_generator_report.py -q` 仍有既有 legacy snapshot failures；本輪 focused future-watch 路徑通過。
