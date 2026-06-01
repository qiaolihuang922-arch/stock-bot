# DISPATCH.md

新對話先讀 `AGENTS.md`、本文件、`CURRENT_STATE.md`。本文件只保留接力必需資訊。

## Current Task

- task_id: `holding-weak-observation-clock-20260601`
- task_name: `Holding Weak Observation Clock`
- task_type: `normal_patch`
- owner_status: `reported_holding_weak_watch_lacks_observation_days`
- architect_status: `qa_passed_pending_git_close`
- pm_status: `done`
- tech_status: `done`
- qa_status: `passed`
- latest_commit: see `git log -1`

## Current Follow-up

- task_id: `report_v20_4_21_afterhours_brief_evidence_merge`
- task_name: `V20.4.21 Afterhours Brief Evidence Merge`
- task_type: `normal_patch`
- architect_status: `qa_passed_pending_git_close`
- qa_status: `passed`

## Current Result

- 任務一已完成並推送：commit `1f9601d fix wait breakout rr gap reason`，Git completion gate passed。
- 任務三已完成並推送：commit `dcc0cd5 cleanup unused analysis locals`，Git completion gate passed。
- 任務四已完成並推送：commit `bc73f7f use structured brief warning flags`，Git completion gate passed。
- 任務二目前 blocked，未吸收產品 diff。
- 阻塞原因：QA runner timeout / stream disconnected before final sentinel；捕獲輸出已指出版本契約風險：support stop candidate 會改變使用者可見 `stop / risk / rr`，但 VERSION 未升且沒有 Owner 放行。
- Tech candidate 留在 tech worktree：`services/analysis.py`、`tests/test_analysis_engine.py`；主 repo 未吸收該產品 diff。
- 本輪修最新報文衝突第一優先級：盤後第三則「今日無有效新倉」與第一則今日買入持倉矛盾。
- 修正：盤後第三則納入 holding_items 中 today buy holding；有今日買入持倉時顯示「今日交易：已建立新倉 N 檔」並保留「新增有效進場：無」。
- QA：Re-QA `通過`；按手機閱讀順序確認第一則今日買入、第三則不再否定今日新倉；負面案例無 today buy 不誤報。
- 本輪修最新報文衝突第二優先級：光寶科今日買入但盤後盤面弱勢 / 遠離突破，容易被誤讀成當前仍可買。
- 修正：報文版本升 `v20.4.22`；盤後今日買入持倉若當前不滿足買點，持倉卡新增來源 / 限制說明，區分策略盤中已執行、手動/ledger、unknown fail-closed。
- QA：Re-QA `通過`；確認無 buy_source 但有 ledger event 時不默認策略 BUY，distance > 4 弱勢 can_buy probe passed，message order / DB / live Telegram / holding state 未改。
- 本輪修最新報文衝突第三優先級：技嘉類 `可準備｜過熱降溫` 但 `RR 0.00（不足）` 與其他過熱股 `RR -（過熱）` 不一致。
- 修正：未持倉 RR 顯示新增窄條件，過熱 blocker 且 `rr=0` 時顯示 `RR -（過熱）`；非過熱 `rr=0` 與持倉路徑不變。
- QA：Re-QA `通過`；確認技嘉類卡片手機順序為過熱降溫 / 待降溫 / RR 過熱，非過熱與持倉反證通過。
- 本輪修最新報文衝突第四優先級：群創 / 仁寶類縮量漲停與緯創 / 英業達類攻擊量漲停在可準備文案中被等同。
- 修正：報文版本升 `v20.4.23`；未持倉 `漲停鎖價` 且 `volume_ratio < 1.0` 時，卡片與強勢準備摘要顯示 `縮量漲停，需開板回測確認，不等同攻擊量`；`volume_ratio >= 1.0` 或非漲停不顯示。
- QA：Re-QA `通過`；補 `V=1.0` 邊界與低量非漲停反證；確認分組 / decision 不變、未改策略 / DB / live Telegram。
- 本輪修最新報文衝突第五優先級：智原類弱勢遠離持倉只有「續抱觀察 / 降低優先級」，沒有觀察第幾天或資料未確認狀態。
- 修正：報文版本升 `v20.4.24`；弱勢遠離且續抱觀察持倉若 `holding` 或 dict-shaped `position_events` 有可信正整數觀察天數，條件行顯示 `弱勢觀察第 N 天` 與下一日降級條件；缺可信來源顯示 `觀察天數未確認`。list-shaped `position_events` fail-closed，不 crash。
- QA：最終 Re-QA `通過`；完整 `formatTelegramMessages()` probe 覆蓋 holding / dict events 正例、list / top-level / result / invalid fail-closed、主決策不變、未改策略 / DB / live Telegram。
- Git completion gate：final 前必須以 `tools/cao_agent/check_git_completion_gate.sh` 驗證 `main` matches `origin/main` 且 worktree clean。
- 上一輪 v20.4.21 報文修正已在 commit `b177345 restore afterhours control summary` 推送，本輪不再改動該產品 diff。
- 已吸收內容：
  - `presentation/report.py` 將 `交易證據日` 改為短期背景 / 短期背景資料。
  - 盤後 `盤中先觀察` / `盤中觀察修復狀況` 改為明日語境。
  - 盤後未持倉卡片不再逐張輸出長資料來源句。
  - 第三則資料依據改為：持倉與價格支持風控；未持倉只支持分類觀察，不支持直接進場。
  - VERSION 仍為 `v20.4.21`；strategy decision、RR 計算、holding_status、DB write path 無變更。
- 驗證：
  - QA 結論：`通過`。
  - Re-QA output：`.cao_agent_context/outputs/20260601_181248_1516_stock_qa_code_readonly.answer.txt`，結論 `通過`。
  - `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m py_compile presentation/report.py tests/test_generator_report.py tests/test_market_theme_evidence.py`：passed。
  - `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py tests/test_market_theme_evidence.py`：128 passed，181 warnings。
  - QA source-error phone-order probe：passed。
  - `git diff --check`：passed。
  - scoped diff：`presentation/report.py`、`tests/test_generator_report.py`、`tests/test_market_theme_evidence.py`、固定 handoff Markdown。
- Follow-up 驗證：
  - 盤後第三則恢復 `持倉風控檢查` 與 `未持倉漏斗（非執行）`。
  - 資料依據合併市場短期背景、持倉數、未持倉分類數、執行記憶邊界與持倉 RR 邊界。
  - Re-QA output：`.cao_agent_context/outputs/20260601_185800_22905_stock_qa_code_readonly.answer.txt`，結論 `通過`。
  - `tests/test_generator_report.py`：92 passed，181 warnings。
  - presentation boundary gate：未新增 DB writer、evidence writer、schema alter 或 fake production path。

## Next Action

- 收口：commit / push 後跑 `tools/cao_agent/check_git_completion_gate.sh`。
- 後續：若 Owner 要真正顯示長期第 N 天，需要另開 production source / observation start 資料治理；本輪只保證有可信來源時顯示、缺來源時不假造。
- 後續同類報文任務：先補或更新手機閱讀 probe，再改 formatter；不要只寫規則。
- 旁支另開：Telegram reply markup 仍附在最後一則 message，新 message order 下可能需要 delivery consumer 任務評估按鈕落點。
- 旁支另開：如果 Owner 認定 2356 英業達實際未賣，需查 production ledger/source truth 為何目前為 `shares=0 / CLOSED`；本輪未寫 DB、不校正 ledger。

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
