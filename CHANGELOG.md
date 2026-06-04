# CHANGELOG:

## 任務尺寸與風險

- 任務尺寸：normal_patch。
- 風險：GitHub Actions 手動入口清理；不影響 Telegram 報文、策略、DB、live delivery。

## 修改內容

- 刪除舊 workflow file：`.github/workflows/stock-bot.yml`。
- 新增乾淨 workflow file：`.github/workflows/stock-bot-clean.yml`。
- workflow 顯示名稱改為 `Stock Bot`，避免手機端沿用舊 `Stock Bot Pro` / old path 的 dispatch form cache。
- workflow_dispatch inputs 只保留 `run_mode`，choices 只保留 `bot`、`daily_evidence`。
- `tests/test_workflow_runtime_config.py` 改讀新 workflow file，並新增舊欄位 / 舊 workflow file 不存在的反證。

## 修改檔案

- `.github/workflows/stock-bot-clean.yml`
- `.github/workflows/stock-bot.yml`
- `tests/test_workflow_runtime_config.py`
- `TASK.md`
- `CHANGELOG.md`
- `QA_REPORT.md`
- `DISPATCH.md`
- `CURRENT_STATE.md`
- `CLEANUP_PLAN.md`

## 契約影響

- GitHub Actions 手動執行入口只接受 `run_mode`。
- 舊 `start_date` / `end_date` / `backfill_version` / `backfill_may` / `backfill_and_bot` 不再是 workflow contract。
- scheduled daily evidence 與 bot run steps 保持原行為。

## 未影響模組

- 未改 `core/generator.py` VERSION。
- 未改策略 decision、RR、持倉風控。
- 未改 DB schema / write path。
- 未做 live Telegram。

## 自檢命令與結果

- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/workflow_clean_inputs_pytest arch -arm64 ./.venv/bin/python -m pytest tests/test_workflow_runtime_config.py -q` -> 9 passed。
- `git diff --check` -> passed。
- `find .github/workflows -maxdepth 1 -type f -print` -> only `.github/workflows/stock-bot-clean.yml`。

## 覆蓋層級

- workflow yaml：covered。
- runtime config shell script extraction：covered。
- manual UI schema text contract：covered by workflow text assertions。
- GitHub mobile app live UI：未直接操作；需 push 後在 GitHub app 重新開新的 `Stock Bot` workflow 驗證。

## 殘留風險

- GitHub mobile app 可能仍暫時顯示已刪除的舊 workflow 歷史項目；應改點新的 `Stock Bot` workflow。
- 若 GitHub app 本地 cache 未刷新，需關閉重開 app 或從 Actions workflow list 選新名稱。
