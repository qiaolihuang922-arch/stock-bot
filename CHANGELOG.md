# CHANGELOG:

## 任務尺寸與風險

- 任務尺寸：normal_patch。
- 風險：GitHub Actions schedule 分流錯誤會讓 scheduled TG bot 永遠不跑。

## 修改內容

- `.github/workflows/stock-bot-clean.yml`
  - 保留 `0 6 * * 1-5` 作為 `daily_evidence` schedule。
  - 新增 `10 6 * * 1-5` 作為 `bot` schedule。
  - 三個 workflow step 的 `RUN_MODE` expression 改為依 `github.event.schedule` 明確分流，不再把所有 schedule 都導向 `daily_evidence`。
- `tests/test_workflow_runtime_config.py`
  - 反證 workflow 同時存在 daily evidence 與 bot schedule。
  - 反證 `daily_evidence` 仍 skip `Run bot`。
  - 新增 fake-python dry-run，確認 `RUN_MODE=bot` 會呼叫 `python main.py`，不觸發 live network。
- `tools/cao_agent/run_online_agent.sh`
  - 啟動 online PM/QA runner 前呼叫 `ensure_agent_dirs`，確保 CAO log 目錄存在。

## 修改檔案

- `.github/workflows/stock-bot-clean.yml`
- `tests/test_workflow_runtime_config.py`
- `tools/cao_agent/run_online_agent.sh`
- `TASK.md`
- `CHANGELOG.md`
- `QA_REPORT.md`
- `DISPATCH.md`
- `CURRENT_STATE.md`

## 契約影響

- Telegram 報文版本維持 `v20.4.47`。
- scheduled workflow 恢復 bot delivery chain：schedule -> `RUN_MODE=bot` -> `Run bot` -> `python main.py` -> `send_many()`。
- `daily_evidence` 不要求 Telegram secrets、不跑 live bot delivery。

## 直接消費者同步

- GitHub scheduled runner 可在 daily evidence 之後跑 bot。
- Manual dispatch `run_mode=bot` 行為不變。
- CAO online runner 的 log directory preflight 補齊，但本機仍缺 `cao` / `cao-server` binary，正式 agent runner 未在本輪恢復。

## 未影響模組

- 未改 `main.py`。
- 未改 `services/notifier.py`。
- 未改 generator / presentation / strategy / DB write path。

## 自檢命令與結果

- `.venv/Scripts/python.exe -m pytest tests/test_workflow_runtime_config.py -q` -> 10 passed。
- `.venv/Scripts/python.exe -m pytest tests/test_main_delivery_guard.py tests/test_notifier.py -q` -> 5 passed。
- `.venv/Scripts/python.exe -m py_compile main.py services/notifier.py tests/test_workflow_runtime_config.py tests/test_main_delivery_guard.py tests/test_notifier.py` -> passed。

## 覆蓋層級

- runner artifact / log：本輪先抓到 CAO PM runner log directory missing，已補 preflight；之後確認本機缺 `cao-server` binary，無法使用 CAO agent runner。
- workflow dry-run：fake-python 驗證 `RUN_MODE=bot` 會進 `python main.py`。
- delivery guard：`main.py` 失敗不 mark sent、成功才 mark sent。
- notifier：多則訊息與 reply markup 行為未回退。

## 殘留風險

- 未做 live Telegram delivery。
- 未讀 GitHub production run log；本輪以 repo workflow 與 dry-run shell step 反證 schedule 分流。
- 本機 CAO binary 缺失仍是 runner 環境問題，已避免影響本輪產品修復，但後續若要恢復 agent runner 需另補安裝。
