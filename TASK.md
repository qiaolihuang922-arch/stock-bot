# TASK: Phase 3 自動化證據生產常態化

## 任務狀態

- task_id：phase3-evidence-automation-20260602
- 任務類型：major
- 狀態：ready_for_tech
- QA 分級建議：L3
- 判定理由：本輪接入 GitHub Actions / scheduled runner 與 approved production write path，涉及 production evidence 寫入、盤後工作日觸發、write guard、smoke、read-after-write 與 stale 告警；雖不改 DB schema 與策略分數，
但觸及正式寫入流程。
- 版本建議：若新增或改變使用者可見報文 / 日誌告警文字，需同步升版或更新對應 header / 常量；若只改 workflow / script / tests 且無報文可見輸出，版本可不升。

## Owner 問題

Phase 1/2/2b major 前，證據鏈需先常態可用。上一輪 Phase 3 自動化證據生產被 stale Tech worktree 阻塞，本輪要重跑並收斂成可驗收任務。

要解決三個問題：

1. daily_signal_snapshot 是否能在每個盤後工作日穩定寫入，避免 record_daily_snapshots 或 13:20+ 盤後觸發條件漏跑。
2. market_theme_confirmed_evidence 是否能每交易日自動回填 confirmed 行，且只走既有 approved write path。
3. 證據連續 N 日 unavailable / stale 時，需有報文或日誌告警，避免後續加權或 decision score 靜默失效。

## 使用者可見結果

- 盤後工作日約 13:20+ 的自動流程可穩定產出 daily_signal_snapshot 與 market_theme_confirmed_evidence confirmed 行。
- 若證據連續缺失或 stale，Owner 能在 workflow log 或 dry-run 報文 fixture 中看到可讀告警。
- 本輪不 live 發 Telegram；若 Tech 選擇把告警接入報文 builder，只能用測試 / fixture / dry-run 驗證。

手機 / 日誌閱讀路徑：

- 報文告警需出現在 summary 或 evidence/status 區塊，不得混入可買、推薦、準備買入語氣。
- workflow log 告警需是固定可 grep 單行，避免被 debug log 淹沒。

示例輸出形狀：

⚠️ 證據告警
market_theme_confirmed_evidence：連續 2 個交易日 unavailable/stale，今日不作為加權依據。
daily_signal_snapshot：盤後快照缺失，請檢查 scheduled workflow / write guard。

或 workflow log：

EVIDENCE_STALE_ALERT source=market_theme_confirmed_evidence consecutive_days=2 status=stale action=fail_closed
EVIDENCE_WRITE_CONFIRMED source=daily_signal_snapshot trading_day=2026-06-02 read_after_write=ok

## 非目標

- 不改 evidence_score。
- 不改 final_confidence。
- 不改 decision_eligible。
- 不改 funnel evidence modifier。
- 不改 RR 公式。
- 不改策略核心、持倉建議、買賣 / 加減碼 / 停損停利 decision。
- 不新增或修改 DB schema / RLS / grant / policy / role / index / constraint。
- 不手寫 production DML。
- 不 live Telegram delivery。
- 不把 local cache、runtime dict、agent 對話當跨日 source-of-truth。
- 不把本輪擴成 Phase 1/2/2b 決策分數接入。

## 影響模組與直接消費者

影響模組：

- record_daily_snapshots 相關 script / runner / workflow。
- write_market_theme_confirmed_evidence.py 或既有等價 approved write script。
- GitHub Actions / scheduled workflow / 既有 runner 的盤後觸發條件。
- evidence stale / unavailable monitor 或報文 / log alert 產生位置。
- tests / probes / fixtures，覆蓋 workflow command、guard failure、read-after-write、非交易日與非盤後條件。

直接消費者：

- GitHub Actions scheduled runner。
- production DB 既有 evidence / snapshot 寫入接口。
- 後續 Phase 1/2/2b decision score 讀取證據鏈的流程。
- Owner 手機閱讀的 Telegram 報文 fixture 或 workflow log。
- QA L3 驗收 probes。

## 輸出契約

daily_signal_snapshot：

- 僅交易日盤後可寫入，保守以 13:20+ 作為可測門檻。
- 非交易日或非盤後不得誤寫。
- 只能走既有 approved script / service / workflow path。
- 必須可重跑；重跑不得製造不可控重複資料或錯誤覆蓋。
- 必須有 read-after-write 或等價查核證據。
- 漏跑、guard failure、read-after-write failure 必須 fail closed 並產生可讀 log / alert。

market_theme_confirmed_evidence：

- 每交易日 scheduled / runner 產生 confirmed row。
- 必須接入 write_market_theme_confirmed_evidence.py 或既有等價 approved write script。
- 必須保留且不得弱化 6 層 write guard：credential、source_family、payload、secret、write、smoke。
- 必須保留 read-after-write 校驗。
- guard failure、smoke failure、read-after-write failure 均需 fail closed，不得吞錯後宣告成功。

stale / unavailable 監控：

- N 預設為連續 2 個交易日。
- 只計交易日；非交易日不增加連續日。
- unavailable 與 stale 均納入。
- 告警可在 workflow log 或 dry-run 報文 fixture 呈現。
- 告警需包含 source、consecutive_days、status、action。
- action 必須表明 fail_closed 或 not_used_for_weighting，不得像推薦或可買訊號。

## 版本契約

已存在且不得回退的契約：

- 既有 approved write path / script contract 不得被繞過。
- write_market_theme_confirmed_evidence.py 既有 6 層 guard 不得刪除、短路或改成 best-effort。
- read-after-write 校驗不得移除。
- production DB schema / RLS / grant / policy / role 不得變更。
- live Telegram delivery 仍需 Owner 單獨批准。
- evidence_score / final_confidence / decision_eligible / funnel evidence modifier 不得因本輪變更而改變。
- local cache、worktree、runtime dict、agent 對話不得成為跨日 source-of-truth。

若現有 workflow、script 名稱、報文版本常量或 evidence table 欄位與上述稱呼不一致，Tech 必須以 repo 內既有契約為準定位；若找不到 approved write path 或 table contract 無法確認，回報 blocked，不得自行創建 schema 或手寫
DML。

## 驗收條件

1. 交易日盤後 workflow / runner probe 可重跑，能跑通 daily_signal_snapshot command、market_theme_confirmed_evidence write command、smoke guard、read-after-write check。
2. 非交易日 probe 不誤寫 snapshot 或 confirmed evidence，log 清楚顯示 skipped reason。
3. 非盤後交易日 probe 在 13:20 前不得誤寫，log 清楚顯示 skipped reason。
4. guard failure probe 覆蓋 credential / source_family / payload / secret / write / smoke 任一失敗均 fail closed，exit status 不得偽成功，不得吞錯後繼續寫入或宣告 confirmed。
5. read-after-write failure probe 在寫入後讀不到 expected row 時 fail closed，log / alert 可定位 source 與 trading_day。
6. stale / unavailable 連續 2 個交易日 probe 產生告警；非交易日不增加連續日；告警文字在手機或 workflow log 中可讀，且不被誤讀為買入建議。
7. QA L3 必須額外檢查 GitHub workflow 是否真的接入 scheduled / existing runner，而不只是 local script 測試。
8. QA L3 必須檢查 scripts 仍走 approved write path，production write guard 未被繞過。
9. QA L3 必須補一個 Tech 未覆蓋的直接消費者、負面案例、手機 / log 誤讀路徑或契約風險 probe。

## 範例或 Fixture

case: trading_day_after_close
now: 2026-06-02 13:25 Asia/Taipei
expected:
daily_signal_snapshot: write_attempted_and_read_after_write_ok
market_theme_confirmed_evidence: confirmed_row_read_after_write_ok
alert: none

case: trading_day_before_close
now: 2026-06-02 12:30 Asia/Taipei
expected:
daily_signal_snapshot: skipped
market_theme_confirmed_evidence: skipped_or_not_scheduled
reason: before_after_close_window
write: none

case: non_trading_day
now: 2026-06-06 13:25 Asia/Taipei
expected:
daily_signal_snapshot: skipped
market_theme_confirmed_evidence: skipped
reason: non_trading_day
write: none

case: stale_two_trading_days
source: market_theme_confirmed_evidence
statuses:
2026-06-01: stale
2026-06-02: unavailable
expected_alert:
source: market_theme_confirmed_evidence
consecutive_days: 2
action: fail_closed_or_not_used_for_weighting

case: guard_failure
guard: payload
expected:
write: none
exit_status: failed
log_contains: guard failure
read_after_write: not_claimed_ok

## 明確禁止事項

- 禁止新增 DB schema / RLS / grant / policy / role / index / constraint。
- 禁止手寫 production DML。
- 禁止繞過 write_market_theme_confirmed_evidence.py 或既有 approved write interface。
- 禁止移除、弱化、短路 6 層 write guard。
- 禁止把 guard failure 當 warning 後繼續成功。
- 禁止把 read-after-write failure 宣告為成功。
- 禁止 live Telegram delivery。
- 禁止修改 evidence_score、final_confidence、decision_eligible、funnel evidence modifier。
- 禁止修改 RR 公式或策略 decision。
- 禁止把 stale worktree 內的旁支 diff 混入本輪。

## 阻塞條件

- 找不到既有 approved write path / script，或無法確認 write_market_theme_confirmed_evidence.py 等價接口。
- 現有 DB contract 不足以 read-after-write，但需要新增 schema / 欄位才能完成。
- GitHub Actions production write workflow 需要 secret / credential 但 repo 無法提供安全 guard 或 smoke 驗證。
- Tech worktree stale，含與本輪無關但會影響 workflow / script / tests 的舊 diff。
- 測試環境無法重跑 workflow / script probes，且無法補環境。
- guard failure 或 source-error 只能被吞錯，無法 fail closed。
- 任一驗收需要 live Telegram 或手寫 production DML 才能完成。

## 本輪停止條件

完成到以下範圍即停止：

- 交易日盤後、非交易日、非盤後、guard failure、read-after-write failure、stale/unavailable 連續 2 個交易日全部有可重跑 tests / probes。
- GitHub workflow / scheduled runner 已接入 daily_signal_snapshot 與 market_theme_confirmed_evidence approved write command。
- workflow log 或 dry-run 報文 fixture 已能顯示 evidence stale/unavailable 告警。
- QA L3 完成 workflow、script guard、手機 / log 可讀風險與至少一個額外反證。

以下旁支不納入本輪，若發現只記待辦或 blocked，不順手實作：

- evidence_score / final_confidence / decision_eligible / funnel modifier 接入。
- RR 或策略 decision 調整。
- DB schema / RLS / grant / policy / role 變更。
- production historical bulk backfill 超出每交易日 confirmed row 自動化。
- live Telegram delivery。
- 其他報文文案清理或策略顯示修正。
