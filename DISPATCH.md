# DISPATCH.md

依 `AGENTS.md` 啟動順序閱讀；本文件只保留任務看板、handoff 指針與固定啟動命令。

- task_md_holds: `recently_done`
- task_md_task_id: `phase0-bugs-pre-evidence-score-20260602`
- task_md_note: `TASK.md / CHANGELOG.md / QA_REPORT.md 目前是最近完成任務的滾動 handoff，不代表仍在 Tech/QA。`

## Active

- none

## Queued

- none

## Recently Done

- `pending-commit`｜`phase0-bugs-pre-evidence-score-20260602`｜risk_patch｜Owner major 指令前置：Phase 0 顯示門控回歸、B1 去除 `觀察：觀察`、B2 弱勢/遠離突破不得顯示 `極強`、B3/B4 持倉風控全列與排序一致回歸、B5 `隔日確認` 獨立漏斗 bucket；版本升 `v20.4.29`；QA passed；主 repo `tests/test_generator_report.py` 119 passed。
- `7a02188`｜`holdings-risk-list-no-truncation-20260602`｜normal_patch｜持倉風控檢查不再預設截斷前 5 筆；有幾檔持倉就列幾檔，不顯示 `另有 N 項持倉風控見詳情`；排序與持倉卡 / detail index 同源；版本升 `v20.4.28`；QA passed；主 repo `tests/test_generator_report.py` 116 passed。
- `cb3e47d`｜`20260602-risk-codex-fixlist-closeout-4-12`｜risk_patch｜Owner 修復清單第 4/5/6/7/9/12 與第 8/10/11 回歸一次收口：strategy sample 改結構化 status、market/theme 可靠度去硬編碼、cross_day source gate、LAST_OHLCV stale 標注、summary 降噪、0-count / 空占位隱藏、持倉排序 / 主行動回歸、已突破負百分比人話化；版本升 `v20.4.27`；QA passed；主 repo `tests/test_generator_report.py tests/test_stock_api_history.py` 125 passed。
- `d432545`｜`risk_patch_unheld_funnel_overheat_prepare_fix`｜risk_patch｜清單第 3 項：過熱 / RR blocker / 過熱降溫未持倉不再計入 `可準備`，改入 `等冷卻 / 等回測` 僅追蹤；普通非過熱突破回測仍保留可準備；版本升 `v20.4.26`；QA passed；主 repo `tests/test_generator_report.py` 112 passed。

## Blocked / Deferred

- `strategy-support-stop-candidate-20260601`：blocked，未吸收產品 diff。原因：support stop candidate 會改變使用者可見 `stop / risk / rr`，但 VERSION / Owner 放行契約未完成。主 repo 未吸收 `services/analysis.py` / `tests/test_analysis_engine.py` candidate diff。
- production source follow-up：若 Owner 要長期顯示持倉觀察第 N 天，需另開 observation start / observation days 持久來源治理；本輪只保證有可信來源時顯示、缺來源時不假造。

## Next Action

- Owner major 指令下一步：Phase 3 自動化證據生產，先讓 strategy / market evidence 常態可用；完成後再進 Phase 1/2/2b evidence_score / final_confidence / funnel modifier major。
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
