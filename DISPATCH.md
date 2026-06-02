# DISPATCH.md

依 `AGENTS.md` 啟動順序閱讀；本文件只保留任務看板、handoff 指針與固定啟動命令。

- task_md_holds: `recently_done`
- task_md_task_id: `20260602_intraday_v20_4_24_a1_a2_a3_hard_conflicts`
- task_md_note: `TASK.md / CHANGELOG.md / QA_REPORT.md 目前是最近完成任務的滾動 handoff，不代表仍在 Tech/QA。`

## Active

- none

## Queued

- none

## Recently Done

- `dab598e`｜`20260602_intraday_v20_4_24_a1_a2_a3_hard_conflicts`｜normal_patch｜06/02 盤中報文 A1/A2/A3 硬衝突：不可買未持倉不再以可準備主標籤呈現；持倉主行動與排序跨卡片 / 風控 / 索引一致；`v20.4.25`；QA passed；Git completion gate passed。
- `33cbc4b`｜`mark-bot-workflow-fix-pushed-20260602`｜process_governance｜校正 DISPATCH / CURRENT_STATE 中上一輪 run-bot workflow fix 的 pending 狀態；scope gate passed；Git completion gate passed。
- `c6da0bf`｜`fix-bot-workflow-may-backfill-guard-20260602`｜normal_patch｜GitHub Actions default `run_mode=bot` 跳過 May market/theme backfill，避免 2026-06-02 range guard 阻塞；QA passed；Git completion gate passed。
- `a1ea855`｜`process-dispatch-state-machine-and-profile-boundaries-20260602`｜process_governance｜DISPATCH 三段狀態機、rolling handoff 指針、Architect 角色卡、角色卡機讀 sections / conflict priority / shared boundaries、agent profile contract gate；scope gate passed。
- `254f909`｜`holding-weak-observation-clock-20260601`｜normal_patch｜弱勢遠離持倉觀察天數 / fail-closed；`v20.4.24`；QA passed；Git completion gate passed。

## Blocked / Deferred

- `strategy-support-stop-candidate-20260601`：blocked，未吸收產品 diff。原因：support stop candidate 會改變使用者可見 `stop / risk / rr`，但 VERSION / Owner 放行契約未完成。主 repo 未吸收 `services/analysis.py` / `tests/test_analysis_engine.py` candidate diff。
- production source follow-up：若 Owner 要長期顯示持倉觀察第 N 天，需另開 observation start / observation days 持久來源治理；本輪只保證有可信來源時顯示、缺來源時不假造。

## Next Action

- 等 Owner 下一個任務。
- 開新任務前先看 `task_md_holds`，不要用 `TASK.md` 內部舊狀態反推當前看板。
- 報文 / 策略 / 產品修復仍走 PM -> Tech -> QA；流程治理文件可由 Architect 直接改。

## Fixed Commands

Owner 對 Architect：

```text
你是 Architect / 總控，不是 PM、Tech、QA。依 AGENTS.md 啟動順序讀文件；產品/策略/報文 feature 先分派 PM，不直接寫產品代碼。
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
