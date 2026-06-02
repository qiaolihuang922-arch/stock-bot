# CHANGELOG:

## 任務尺寸與風險

- 任務類型：normal_patch。
- 風險判斷：影響 GitHub Actions workflow 條件與對應測試；不改策略、DB schema、Telegram 報文或 production write guard。

## 修改內容

- 修正 `.github/workflows/stock-bot.yml`：`Backfill official market/theme evidence` step 只在 `run_mode=backfill_may` / `run_mode=backfill_and_bot` 執行。
- `run_mode=bot` 現在明確 log：`May market/theme evidence backfill skipped for run_mode=bot`，不會呼叫 `scripts/backfill_market_theme_sources.py --write --confirm-write`。
- 補 workflow shell step 模擬測試，驗證 bot skip、backfill modes 仍執行且 guard failure 不被吞掉。

## 修改檔案

- `.github/workflows/stock-bot.yml`
- `tests/test_workflow_runtime_config.py`

## 最小改動策略

- 只收窄 May market/theme backfill workflow 條件。
- 不修改 `scripts/backfill_market_theme_sources.py` 的 May range guard 或 DB 寫入邏輯。
- 測試直接抽取 workflow run block 執行，避免只做 YAML 字串檢查。

## 契約影響

- `run_mode=bot`：不再執行 May-only market/theme evidence write step。
- `run_mode=backfill_may`：仍執行 May market/theme evidence backfill；越界 source date 仍 fail closed。
- `run_mode=backfill_and_bot`：仍先執行 May market/theme evidence backfill；若 guard 失敗，workflow step 失敗，不假成功進 bot。
- 未改 CLI 參數、payload、message list、Telegram 版本、DB contract。

## 直接消費者同步

- GitHub Actions `Stock Bot Pro / run-bot` job 已同步 workflow 條件。
- 手動 `workflow_dispatch` 預設 `run_mode=bot` 已同步 skip May backfill。
- May evidence backfill 操作者仍使用既有 `backfill_may` / `backfill_and_bot` 名稱與語意。

## 未影響模組

- Telegram 報文內容與版本。
- strategy decision / RR / 持倉狀態機。
- DB schema、RLS、grant、policy、role、index、constraint。
- `scripts/backfill_market_theme_sources.py` production safety guard。
- Node.js 20 deprecation warning。

## 已跑自檢命令

- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_bot_pycache .venv/bin/python -m pytest -q tests/test_workflow_runtime_config.py tests/test_market_theme_source_backfill.py`：21 passed。
- `git diff --check`：passed。

## 殘留風險

- 未跑 GitHub Actions live workflow。
- 未使用 production secrets。
- 未做 live Telegram 或 Supabase write。
- 本輪只以本地 workflow shell 模擬與既有 guard 單元測試驗證。

## 旁支待辦

- Node.js 20 deprecation warning 另開任務處理。
- GitHub Actions 全面整理不在本輪。
- 市場 / 題材策略重新設計不在本輪。
