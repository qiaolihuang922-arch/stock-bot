# DISPATCH.md

依 `AGENTS.md` 啟動順序閱讀；本文件只保留任務看板、handoff 指針與固定啟動命令。

- task_md_holds: `recently_done`
- task_md_task_id: `fix_market_theme_evidence_gate_v20_4_31`
- task_md_note: `TASK.md / CHANGELOG.md / QA_REPORT.md 目前是最近完成任務的滾動 handoff，不代表仍在 Tech/QA。`

## Active

- none

## Queued

- none

## Recently Done

- `pending`｜`fix_market_theme_evidence_gate_v20_4_31`｜normal_patch｜不升版仍維持 `v20.4.31`：market/theme confirmed_trend 不再疊 15 日二次門檻；per-stock 缺 market_theme fallback report-level market evidence；英業達卡片顯示 `證據 +8%（supporting）` 而非不適用；strategy 跨版本回測 filter 回歸通過；QA passed；主 repo targeted tests 4 passed。
- `32d7422`｜`evidence-wiring-and-funnel-consistency-20260602`｜risk_patch｜不升版仍維持 `v20.4.31`：strategy evidence loader 移除 version filter，跨版本 outcomes 可進樣本；market/theme string summary path 傳入 trade_date 並消費 confirmed evidence_trend；D2/B5 `等冷卻 / 隔日確認` 漏斗與卡片 rendered message 一致；QA passed；主 repo targeted tests 4 passed。
- `b83747a`｜`evidence-per-stock-reliability-funnel-phase3-closeout-20260602`｜major｜v20.4.31：evidence score 改為真正 per-stock；per-stock market/theme 與 strategy 缺 payload 時不 fallback report-level；可靠度 insufficient 不再輸出支持語氣；supporting/partial modifier cap；source-error fail closed；`隔日確認` 納入 `僅追蹤` aggregate；Phase 3 guard 回歸；QA passed；主 repo combined targeted suite 191 passed。
- `c7dd94b`｜`evidence-score-decision-funnel-phase1-2-2b`｜major｜evidence_score 接入 final_confidence、pick/sort 與 Phase 2b funnel 邊界；報文分數拆為綜合 / 技術 / 證據；supporting/single_day 不作 strong boundary evidence；missing evidence fail closed；RR / overheat / chase hard blockers 不放寬；mixed adjusted + ordinary prepare 在 Summary / 漏斗 / card / detail / manifest 拆分一致；版本升 `v20.4.30`；QA passed；主 repo `tests/test_generator_report.py` 129 passed。
- `281be20`｜`phase3-evidence-automation-20260602`｜risk_patch｜Phase 3 自動化證據生產：GitHub Actions 新增 `daily_evidence` schedule，不送 Telegram；Phase 3 runner 在 confirmed trading day + 13:20 後才跑 daily snapshot 與 market/theme approved write CLI；TWSE 無法確認交易日 fail closed skip；stale alert 只按 confirmed trading day 累積；QA passed；主 repo phase3 tests 29 passed。

## Blocked / Deferred

- `strategy-support-stop-candidate-20260601`：blocked，未吸收產品 diff。原因：support stop candidate 會改變使用者可見 `stop / risk / rr`，但 VERSION / Owner 放行契約未完成。主 repo 未吸收 `services/analysis.py` / `tests/test_analysis_engine.py` candidate diff。
- production source follow-up：若 Owner 要長期顯示持倉觀察第 N 天，需另開 observation start / observation days 持久來源治理；本輪只保證有可信來源時顯示、缺來源時不假造。

## Next Action

- 本輪 market/theme evidence gate closeout 已 QA passed，待 commit / push / completion gate 後把 `pending` commit hash 補上。
- 下一步若繼續，優先看 production evidence 實際資料品質 / 長期樣本分布，而不是再修框架或文案。
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
