# CHANGELOG:

## 任務尺寸與風險

- 任務尺寸：normal_patch。
- 風險：readonly 即時來源查詢路徑；不改交易策略、DB、live Telegram。

## 修改內容

- `core/future_watch.py`：
  - 新增 MOPS 查詢預算：`max_targets`、`max_queries`、`max_seconds`。
  - 新增 MOPS diagnostics：`query_count`、`target_count`、`budget_exhausted`、`source_error_count`。
  - 新增市場別正規化：上市 / TWSE -> `sii`，上櫃 / TPEX / OTC -> `otc`，興櫃 -> `rotc`，公開發行 -> `pub`。
  - 新增 TYPEK 優先順序與 early stop；已知市場別時，每個月份先查對應 TYPEK，成功、空表或 source-error 後不再橫向掃其他市場別。
  - MOPS POST 補 `encodeURIComponent=1`、`off=1`，並保留既有 `step=1` / `firstin=1`。
  - 目標股票排序改為持倉優先，其次可買 / 準備 / 觀察候選，再到淘汰 / blocked 類。
- `tests/test_generator_report.py`：
  - 補查詢預算測試，反證不會無上限掃所有股票與 TYPEK。
  - 補市場別優先測試，反證上櫃股票先查 `otc` 並查到 rows 後停止橫向掃描。

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

- `collect_mops_events()` 函式多了可選查詢參數與 diagnostics，既有呼叫不需要改。
- 第 4 則 Telegram 可見格式維持 `v20.4.47`，不新增 query diagnostics 到手機報文。
- MOPS 查詢不再盲掃所有目標與 TYPEK；慢接口被查詢預算約束。

## 未影響模組

- 未改交易策略、RR、加減碼、停損停利、持倉狀態機。
- 未改 DB schema / RLS / grant / policy / write path。
- 未做 live Telegram delivery。
- 未改 GitHub workflow。

## 自檢命令與結果

- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/v20_4_47_query_opt2 arch -arm64 ./.venv/bin/python -m pytest tests/test_generator_report.py -k 'v20_4_47_future or v20_4_47_live or v20_4_47_generate_report or mops_query' -q` -> 10 passed。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/v20_4_47_query_opt_pycompile2 arch -arm64 ./.venv/bin/python -m py_compile core/future_watch.py core/generator.py tests/test_generator_report.py` -> passed。
- `git diff --check` -> passed。
- Read-only live smoke with 光寶科 2301：`mops_query_count=2`、`mops_target_count=1`、`mops_budget_exhausted=False`，仍顯示 06/05 / 06/22 法說會。

## 覆蓋層級

- helper：MOPS target sorting / query budget / TYPEK priority covered。
- formatter：既有 future-watch visible message covered by focused tests。
- official report message-list：focused `formatTelegramMessages` / `generate_report(dry_run=True)` retained。
- live smoke：read-only MOPS official path covered；無 DB write、無 Telegram delivery。

## 殘留風險

- 全球事件 official parser 仍可能 fallback seed；本輪只處理查詢接口預算，不做全球 calendar hardening。
- 若上游 payload 沒有市場別，MOPS 仍需按預算掃 TYPEK；後續可從既有股票 metadata 補 `exchange` / `mops_typek`。
- Full `tests/test_generator_report.py -q` 仍有既有 legacy snapshot failures；本輪 focused future-watch 路徑通過。
