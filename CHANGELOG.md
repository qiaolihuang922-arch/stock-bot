# CHANGELOG:

## 任務尺寸與風險

- 任務尺寸：normal_patch。
- 風險：第 4 則 MOPS 即時查詢完整性；不改交易策略、DB、live Telegram。

## 修改內容

- `core/future_watch.py`：
  - MOPS 查詢順序由單檔深度優先改為廣度優先：所有標的先查第一優先 TYPEK，再進下一輪 fallback。
  - `MOPS_DEFAULT_MAX_TARGETS` 由 8 提到 12，`MOPS_DEFAULT_MAX_QUERIES` 由 24 提到 32。
  - 新增 `MOPS_DEFAULT_MAX_ITEMS = 10`，formatter 法說會顯示上限從 5 提到 10。
  - 已知市場別仍會在該月查完對應 TYPEK 後停止；未知市場別不會因單檔 fallback 掃描餓死後排標的。
- `tests/test_generator_report.py`：
  - 新增 regression：12 檔、24 次 query budget 下，第 12 檔第一優先市場別仍能被查到，避免回退到單檔深度優先。

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
- `collect_mops_events()` 查詢完整性提升；既有呼叫不需要改。
- MOPS 法說會段最多顯示 10 筆。

## 未影響模組

- 未改交易策略、RR、加減碼、停損停利、持倉狀態機。
- 未改 DB schema / RLS / grant / policy / write path。
- 未做 live Telegram delivery。
- 未改 GitHub workflow。
- 未改 global / TWSE 查詢邏輯。

## 自檢命令與結果

- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/v20_4_47_mops_breadth2 arch -arm64 ./.venv/bin/python -m pytest tests/test_generator_report.py -k 'v20_4_47_future or v20_4_47_live or v20_4_47_generate_report or mops_query' -q` -> 11 passed。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/v20_4_47_mops_breadth2_pycompile arch -arm64 ./.venv/bin/python -m py_compile core/future_watch.py core/generator.py tests/test_generator_report.py` -> passed。
- `git diff --check` -> passed。
- Official `generate()` read-only smoke：法說會段恢復多檔，包含 06/04 緯創 / 群創、06/05 光寶科 / 聯電 / 仁寶 / 英業達、06/08 英業達、06/09 仁寶、06/22 光寶科。

## 覆蓋層級

- helper：MOPS breadth-first query order and budget regression covered。
- formatter：MOPS 10-item display cap covered by official smoke。
- official report message-list：focused `formatTelegramMessages` / `generate_report(dry_run=True)` retained。
- live smoke：official `generate()` read-only path covered；無 DB write、無 Telegram delivery。

## 殘留風險

- 全球事件 official parser 仍可能 fallback seed；本輪只處理 MOPS 查詢漏查，不做全球 calendar hardening。
- `影響台股` 目前是顯示語意與種子事件選集，不是新增事件影響評分模型；後續若要更精準可新增台股影響分級。
- Full `tests/test_generator_report.py -q` 仍有既有 legacy snapshot failures；本輪 focused future-watch 路徑通過。
