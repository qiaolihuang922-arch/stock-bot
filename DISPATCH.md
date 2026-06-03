# DISPATCH.md

依 `AGENTS.md` 啟動順序閱讀；本文件只保留任務看板、handoff 指針與固定啟動命令。

- task_md_holds: `recently_done`
- task_md_task_id: `20260603_strategy_evidence_report_risk_patch`
- task_md_note: `TASK.md / CHANGELOG.md / QA_REPORT.md 目前是最近完成任務的滾動 handoff，不代表仍在 Tech/QA。`

## Active

- none

## Queued

- none

## Recently Done

- `7ccc808`｜`20260603_strategy_evidence_report_risk_patch`｜risk_patch｜升版 `v20.4.32`：strategy evidence loader 移除 version filter 並以 `.range()` 分頁取得最近 60 個 distinct trade_date；交易執行 / 新倉建議拆分，未持倉可買標示尚未買入 / 建議分批；原因 / 風險按對象拆分；partial +0% 顯示 `僅輔助參考`；同日建倉 hard_stop / 入場價 -3% / 入場 K 低點觸發當日減碼，僅破警戒維持新倉風控觀察；D1 光寶科翻轉 deferred；QA passed；主 repo targeted tests 201 passed；Git completion gate passed。
- `32fcfd8`｜`telegram_message_noise_consistency_20260603`｜normal_patch｜不升版仍維持 `v20.4.31`：首屏市場行去重並改為 compact count；有可買時顯示 `可買N/僅追蹤N/淘汰N`，無可買時維持不可推薦語氣；刪冗餘新倉/背景/持倉行；交易執行短文案；僅追蹤與 cross-day 歷史 token 降噪；淘汰/弱勢不可行動 RR 顯示 `-（不可行動）`；partial +0% 顯示 `僅輔助參考`；QA passed；主 repo `tests/test_generator_report.py` 146 passed。
- `a92a884`｜`presentation_noise_reduction_v20_4_31`｜normal_patch｜不升版仍維持 `v20.4.31`：簡報市場/結論、原因/風險合併；無有效進場時 `追蹤最強` 改為 `僅追蹤`；盤中/盤後正常來源隱藏資料依據、異常才顯示；卡片不可用歷史/回測降噪；B5 Summary / 漏斗 / card 一致；QA passed；主 repo rendered tests 8 passed。
- `0d20b35`｜`per_stock_evidence_score_funnel_p0_p3_20260602`｜risk_patch｜不升版仍維持 `v20.4.31`：strategy setup sample 成為 per-stock 分量；缺 explicit setup fail closed；弱勢 / 失敗 / EXTREME / technical=0 不吃正向 boost；旺宏 / 聯電 modifier 不同；B5 Summary / 漏斗 / card 一致；QA passed；主 repo targeted tests 4 passed。
- `c4c8b0e`｜`fix_market_theme_evidence_gate_v20_4_31`｜normal_patch｜不升版仍維持 `v20.4.31`：market/theme confirmed_trend 不再疊 15 日二次門檻；per-stock 缺 market_theme fallback report-level market evidence；英業達卡片顯示 `證據 +8%（supporting）` 而非不適用；strategy 跨版本回測 filter 回歸通過；QA passed；主 repo targeted tests 4 passed。
- `32d7422`｜`evidence-wiring-and-funnel-consistency-20260602`｜risk_patch｜不升版仍維持 `v20.4.31`：strategy evidence loader 移除 version filter，跨版本 outcomes 可進樣本；market/theme string summary path 傳入 trade_date 並消費 confirmed evidence_trend；D2/B5 `等冷卻 / 隔日確認` 漏斗與卡片 rendered message 一致；QA passed；主 repo targeted tests 4 passed。

## Blocked / Deferred

- `strategy-support-stop-candidate-20260601`：blocked，未吸收產品 diff。原因：support stop candidate 會改變使用者可見 `stop / risk / rr`，但 VERSION / Owner 放行契約未完成。主 repo 未吸收 `services/analysis.py` / `tests/test_analysis_engine.py` candidate diff。
- production source follow-up：若 Owner 要長期顯示持倉觀察第 N 天，需另開 observation start / observation days 持久來源治理；本輪只保證有可信來源時顯示、缺來源時不假造。

## Next Action

- 本輪 `20260603_strategy_evidence_report_risk_patch` 已 committed / pushed；Git completion gate passed。
- 下一步若繼續，優先看 production evidence 實際資料品質 / daily_signal_snapshot row density / 長期樣本分布，而不是再修文案。
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
