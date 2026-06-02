# DISPATCH.md

依 `AGENTS.md` 啟動順序閱讀；本文件只保留任務看板、handoff 指針與固定啟動命令。

- task_md_holds: `recently_done`
- task_md_task_id: `20260602-risk-codex-fixlist-closeout-4-12`
- task_md_note: `TASK.md / CHANGELOG.md / QA_REPORT.md 目前是最近完成任務的滾動 handoff，不代表仍在 Tech/QA。`

## Active

- none

## Queued

- none

## Recently Done

- `pending-commit`｜`20260602-risk-codex-fixlist-closeout-4-12`｜risk_patch｜Owner 修復清單第 4/5/6/7/9/12 與第 8/10/11 回歸一次收口：strategy sample 改結構化 status、market/theme 可靠度去硬編碼、cross_day source gate、LAST_OHLCV stale 標注、summary 降噪、0-count / 空占位隱藏、持倉排序 / 主行動回歸、已突破負百分比人話化；版本升 `v20.4.27`；QA passed；主 repo `tests/test_generator_report.py tests/test_stock_api_history.py` 125 passed。
- `d432545`｜`risk_patch_unheld_funnel_overheat_prepare_fix`｜risk_patch｜清單第 3 項：過熱 / RR blocker / 過熱降溫未持倉不再計入 `可準備`，改入 `等冷卻 / 等回測` 僅追蹤；普通非過熱突破回測仍保留可準備；版本升 `v20.4.26`；QA passed；主 repo `tests/test_generator_report.py` 112 passed。
- `ffbaf70`｜`risk_patch_score_source_status_display_gate_20260602`｜risk_patch｜顯示門控第 1 項：持倉 / 未持倉卡顯示 S 分數或高置信強弱文字前檢查 `stock.<name>.score.source_status`；score 不足時顯示 `S 證據不足 / S 不可用` 並將盤面降級為待確認；QA passed；主 repo `tests/test_generator_report.py` 111 passed。
- `9b1e084`｜`evidence_gate_p1_p2_p4_20260602`｜risk_patch｜證據鏈第一批硬衝突 P1/P2/P4：strategy_sample 不足時阻斷高置信未持倉行動標籤但不誤傷可用價格；ledger / positions 不足時持倉卡隱藏精確股數 / 均價 / 今日買賣；RR / 過熱 / 證據不足不進可買或進場觸發；`v20.4.25`；QA passed；主 repo `tests/test_generator_report.py` 108 passed。

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
