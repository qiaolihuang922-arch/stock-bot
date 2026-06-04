# CHANGELOG:

## 任務尺寸與風險

- 任務尺寸：tiny_patch。
- 風險：第 4 則台股影響事件手機可見語意；不改交易策略、DB、live Telegram。

## 修改內容

- `core/future_watch.py`：
  - 新增 `_taiwan_market_impact_note()`，依 `impact` 產出台股影響說明。
  - `collect_global_events()` 保留內部 source/source_label，但新增 `impact_note` 給 formatter 使用。
  - `未來30日台股影響事件` 行由 `來源：...` 改為 `說明：...`。
- `tests/test_generator_report.py`：
  - 更新 focused future-watch tests，反證第三段不顯示 `來源：`，每筆事件顯示台股影響說明。

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
- 第三段 Telegram 可見行改為：`日期 事件｜影響面：...｜說明：...`。
- `impact_note` / `reason` 可覆蓋預設說明；缺省時用 `impact` 自動產生說明。
- 歷史類比算法未改，仍是 TWSE 即時 / 近月 OHLC + 壓力模板。

## 未影響模組

- 未改交易策略、RR、加減碼、停損停利、持倉狀態機。
- 未改 DB schema / RLS / grant / policy / write path。
- 未做 live Telegram delivery。
- 未改 GitHub workflow。
- 未改 MOPS / global / TWSE 查詢邏輯。

## 自檢命令與結果

- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/v20_4_47_event_notes arch -arm64 ./.venv/bin/python -m pytest tests/test_generator_report.py -k 'v20_4_47_future or v20_4_47_live or v20_4_47_generate_report or mops_query' -q` -> 11 passed。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/v20_4_47_event_notes_pycompile arch -arm64 ./.venv/bin/python -m py_compile core/future_watch.py core/generator.py tests/test_generator_report.py` -> passed。
- `git diff --check` -> passed。
- Official `generate()` read-only smoke：第三段不再顯示 `來源：`；每筆顯示 `說明：...`，如利率/匯率事件說明外資風險偏好、台股估值、美元/台幣與外資流向。

## 覆蓋層級

- helper：global event impact note generation covered。
- formatter：third section source removal and impact explanation covered。
- official report message-list：focused `formatTelegramMessages` / `generate_report(dry_run=True)` retained。
- live smoke：official `generate()` read-only path covered；無 DB write、無 Telegram delivery。

## 殘留風險

- 全球事件 official parser 仍可能 fallback seed；本輪只處理可見說明，不做全球 calendar hardening。
- `影響台股` 目前是顯示語意與種子事件選集，不是新增事件影響評分模型；後續若要更精準可新增台股影響分級。
- Full `tests/test_generator_report.py -q` 仍有既有 legacy snapshot failures；本輪 focused future-watch 路徑通過。
