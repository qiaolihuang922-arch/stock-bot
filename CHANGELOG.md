# CHANGELOG: docs_local_env_cleanup_20260626

## 修改內容與修改檔案

- `DISPATCH.md`, `CURRENT_STATE.md`, `CLEANUP_PLAN.md`
  - 壓縮上一輪產品修正與環境恢復流水，只保留當前狀態、已完成摘要、待辦。
- `TASK.md`, `CHANGELOG.md`, `QA_REPORT.md`
  - 覆蓋為本輪文件清理 handoff。
- `RESEARCH.md`
  - 保留研究結論，壓縮成高信號摘要。
- `tools/cao_agent/DEPLOYMENT.md`
  - 重寫為 D-drive-first local runbook。
- `tools/cao_agent/local_env.ps1`, `tools/cao_agent/local_env.cmd`
  - 日常啟動只設定 D 槽環境，不寫 Git config。
  - 首次修復 safe.directory/autocrlf 時才使用 `STOCK_BOT_WRITE_GIT_CONFIG=1`。

## 契約影響

- 產品輸出、Telegram 報文、DB 寫入、策略判斷、測試邏輯：無變更。
- 本地開發流程：D 槽工具鏈與 bootstrap 成為標準入口。

## 自檢命令與結果

- UTF-8 readback for fixed Markdown and deployment docs: pass.
- `bash tools/cao_agent/check_architect_edit_scope_gate.sh`: pass.
- `python -m pytest tests/test_generator_report.py -k "low_repair or failed_breakout or rr_blocker or actionability or reclaim or chase_risk or breakout_with_low_rr" -q`
  - Result: `12 passed, 219 deselected`.
- Local dry-run smoke:
  - Flask import OK.
  - `generate_report(dry_run=True)` produced `MESSAGE_COUNT 4`.
- cmd bootstrap smoke: Git/Bash/Python available.

## 殘留風險

- WSL/Node/CAO UI 尚未恢復。
- 舊 `.pytest_cache` 仍需系統權限才能刪除。
