# QA_REPORT:

## 測試範圍

- 任務尺寸 / QA：normal_patch / L2。
- 驗證範圍：GitHub Actions `run_mode` 對 May market/theme evidence backfill step 的條件、對應測試、production guard 是否未被改動。
- 已讀：`TASK.md`、`CHANGELOG.md`、`.github/workflows/stock-bot.yml`、`tests/test_workflow_runtime_config.py`、`tests/test_market_theme_source_backfill.py` 必要 guard 測試脈絡。
- 未跑 live GitHub Actions workflow、production backfill、live Telegram 或 replay。

## 關聯風險掃描

- `TASK.md`、`CHANGELOG.md`、git diff 一致：任務是修正 default `run_mode=bot` 被 May market/theme backfill range guard 阻塞。
- 實際 diff 只把 workflow 條件從包含 `bot` 收窄為只包含 `backfill_may` / `backfill_and_bot`，並新增 workflow shell 模擬測試。
- `run_mode=bot`：workflow log 為 `May market/theme evidence backfill skipped for run_mode=$RUN_MODE`，並 exit 0，不進入 python write step。
- `run_mode=backfill_may` / `backfill_and_bot`：仍進入 `scripts/backfill_market_theme_sources.py --write --confirm-write`。
- Node.js 20 warning 未被處理，符合非目標。
- 未見 DB schema、RLS、grant、policy、role、index、constraint diff。
- 未見 Telegram 報文或 live delivery 路徑 diff。

## 跨區塊語意一致性

- `bot` mode 不執行 May-only backfill write。
- `backfill_may` 與 `backfill_and_bot` 保留 May guard 與 fail-closed。
- workflow log 能區分 skipped / enabled / blocked。
- 未處理 Node.js warning、不改 DB schema / live Telegram。
- 未發現 `TASK.md` / `CHANGELOG.md` / diff 矛盾。

## 使用者誤讀風險

- 本輪沒有 Telegram / summary / dashboard 使用者可見輸出改動，手機閱讀順序不適用。
- workflow log 中 bot mode 明確顯示 May backfill skipped，不會誤讀為 May data 寫入成功。
- backfill modes 明確顯示 May backfill enabled，和 bot skip 分開。

## 質疑與反證

- Tech 自檢重跑：`TMPDIR=.qa_tmp PYTHONPATH=.qa_tmp:. PYTHONPYCACHEPREFIX=.qa_tmp/pycache .venv/bin/python -m pytest -q tests/test_workflow_runtime_config.py tests/test_market_theme_source_backfill.py`：21 passed。
- `git diff --check`：passed。
- QA 補充反證：fake python exit 0 時，`backfill_may` / `backfill_and_bot` returncode 0，各呼叫 `scripts/backfill_market_theme_sources.py` 1 次，且包含 `--write --confirm-write`。
- 負面案例：fake python exit 1 時，bot mode 不呼叫 python；backfill modes 非 0 exit，保留 `source date outside requested May range` failure。

## 未測項目

- 未跑 GitHub Actions live workflow。
- 未使用 production secrets。
- 未做 production DB write / live Telegram delivery。
- 未跑 full repo pytest。
- 未處理 Node.js 20 deprecation warning，符合非目標。

## QA 結論

通過
