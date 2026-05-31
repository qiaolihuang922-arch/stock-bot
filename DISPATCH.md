# DISPATCH.md

新對話先讀 `AGENTS.md`、本文件、`CURRENT_STATE.md`。本文件只保留接力必需資訊。

## Current Task

- task_id: `next_evidence_chain_development`
- task_name: `Continue Evidence Chain Development`
- task_type: `risk_patch`
- owner_status: `requested`
- architect_status: `ready`
- pm_status: `todo`
- tech_status: `todo`
- qa_status: `todo`
- latest_commit: see `git log -1`

## Current Result

- 已推送：
  - `6367d78 fix holiday execution memory report`
  - `4f19e16 docs mark holiday fix pushed`
- 05/31 假日报文主 bug 已修：
  - 英業達 2356 若 production cross-day execution memory 顯示 2026-05-29 已賣 `-112`、`-75`，報文不再輸出「第二段停利，本次建議 56 股」，也不進明日計畫。
  - 若 production source 可讀但 prior take-profit 的 execution memory 缺失或 `sold_shares <= 0`，報文 fail closed：`停利記憶不足`，不輸出明確賣出股數。
  - market/theme evidence 顯示 latest/evidence trade date、holiday report 使用最近交易日 evidence、trend `lookback_range`。
  - `策略證據 v20.0` 已標示為 strategy sample 層，不否定 market/theme production evidence。
- 驗證：
  - QA 結論：`通過`。
  - `PYTHONPATH=. arch -arm64 .venv/bin/python -m pytest -q`：264 passed，153 warnings（第三方 deprecation 類）。
  - `git diff --check`：passed。

## Next Action

下一個新對話要繼續「證據鏈開發」，不是回頭修 05/31 重複停利。

建議第一張 PM 任務：

```text
讓 production market/theme evidence 從「已確認背景」進一步成為可讀的策略輔助層：
1. 不放寬買點、不直接改 BUY/SELL。
2. 把 market/theme trend、lookback_range、support_streak_days 轉成報文中清楚的題材/市場輔助說明。
3. 明確區分：市場/題材 evidence、分類回測 strategy sample、個股買點/風控。
4. 手機閱讀時不得再讓使用者以為 evidence confirmed 等於可以追高。
```

## Fixed Commands

Owner 對 Architect：

```text
你是 Architect / 總控，不是 PM、Tech、QA。先讀 AGENTS.md、DISPATCH.md、CURRENT_STATE.md；產品/策略/報文 feature 先分派 PM，不直接寫產品代碼。
```

Architect 入口：

```text
tools/cao_agent/run_architect_task.sh research "<研究問題>"
tools/cao_agent/run_architect_task.sh plan "<技術規劃問題>"
tools/cao_agent/run_architect_task.sh auto "<Owner 任務>"
```

CAO 服務：

```text
tools/cao_agent/ensure_cao_services.sh
CAO API: http://127.0.0.1:9889/
CAO UI:  http://127.0.0.1:5173/
```
