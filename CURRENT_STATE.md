# CURRENT_STATE.md

新會話短上下文。先讀 `AGENTS.md`、`DISPATCH.md`，再讀本文件。

## Stable Context

- 專案：台股策略 Telegram 報文機器人。
- 正式結果以 git / runner 產生報文為準。
- 使用者可見報文版本在 `core/generator.py` 的 `VERSION`，目前收口目標為 `v20.4.23`。
- 固定 8 份 Markdown 不刪：`AGENTS.md`、`DISPATCH.md`、`RESEARCH.md`、`CURRENT_STATE.md`、`CLEANUP_PLAN.md`、`TASK.md`、`CHANGELOG.md`、`QA_REPORT.md`。
- Architect 是總控；產品 / 策略 / 報文 bug 或 feature 預設走 PM -> Tech -> QA。
- 跨日狀態、已執行交易、歷史 evidence 必須來自 production DB 或 Owner 指定持久來源；local/runtime/worktree 不能當跨日記憶。
- 缺資料、source-error、欄位不足或可信度不足時 fail closed。

## Latest Completed Work

- task_id：`risk_patch_20260531_holiday_report_execution_memory_evidence_dates`
- commits：
  - `6367d78 fix holiday execution memory report`
  - `4f19e16 docs mark holiday fix pushed`
- 結論：05/31 假日报文重複第二段停利已修並推送。
- 關鍵行為：
  - production cross-day execution memory 足夠時，英業達 2356 顯示已執行不重複。
  - prior take-profit guard 存在但 execution memory 缺失或 `sold_shares <= 0` 時，顯示 `停利記憶不足`，不輸出賣出股數，不進明日計畫。
  - market/theme evidence 顯示 actual/latest trade date 與 `lookback_range`。
  - strategy sample 0 與 market/theme production evidence 已分層。
- 驗證：QA `通過`；full pytest 264 passed，153 warnings（第三方 deprecation 類）。

## Current Worktree

- task_id：`pm-normal-limit-up-low-volume-risk`
- 狀態：PM done / Tech done / QA `通過`；主 repo 已吸收可吸收 diff，等待 commit / push / Git completion gate。
- commit：任務二 blocked 文件已在 `9120672 mark support stop task blocked` 推送到 `origin/main`。
- 已完成前置任務：光寶科今日買入盤後不可續買說明已在 `2bd0a48 explain today buy non-current entry` 推送；技嘉過熱 RR 顯示已在 `2036415 show overheat blocker for zero rr` 推送。
- 問題：群創 / 仁寶類 `漲停鎖價` 但 `V < 1.0`，和緯創 / 英業達類攻擊量漲停在可準備文案中被等同。
- 修正：`core/generator.py` 新增 `low_volume_limit_up_risk_text()`；未持倉卡片與第三則強勢準備摘要對 `漲停鎖價 + volume_ratio < 1.0` 顯示 `縮量漲停，需開板回測確認，不等同攻擊量`；`volume_ratio >= 1.0` 或非漲停不顯示。
- 驗證：Re-QA output `.cao_agent_context/outputs/20260601_220302_17956_stock_qa_code_readonly.answer.txt`，結論 `通過`；主 repo targeted py_compile / pytest / diff check passed。
- 邊界：未改 strategy decision、RR 計算、DB write、live Telegram。
- 後續：Owner 同批剩餘問題需拆分處理：智原 observation_days / 觀察天數量化。
- 上一輪 v20.4.21 行為摘要保留如下，供重開對話辨識已落地內容：
- 關鍵行為：
  - 不升 VERSION，仍為 `v20.4.21`。
  - 三日資料改稱短期背景 / 短期背景資料，不再使用交易證據日語感。
  - 盤後下一步改為明日語境。
  - 盤後未持倉卡片移除逐檔長資料來源句。
  - 第三則資料依據改成人話：持倉與價格支持風控；未持倉只支持分類觀察，不支持直接進場。
  - 非加碼持倉不顯示新倉 RR 數字；新倉候選 RR 保留。
  - 今日買入且主行動為 `新倉風控觀察` 時，即使底層 signal 是 `ADD_10 / allow_add=True`，也不顯示具體新倉 RR 數字。
  - 盤後第三則恢復 `持倉風控檢查` 與 `未持倉漏斗（非執行）`。
  - 資料依據改為合併證據摘要：市場短期背景、持倉數、未持倉分類數、執行記憶邊界、持倉 RR 邊界。
  - 不改 strategy decision、RR 計算、holding_status、DB schema/write、live Telegram。
- 驗證：
  - Re-QA output：`.cao_agent_context/outputs/20260601_181248_1516_stock_qa_code_readonly.answer.txt`，結論 `通過`。
  - Follow-up Re-QA output：`.cao_agent_context/outputs/20260601_183214_25279_stock_qa_code_readonly.answer.txt`，結論 `通過`。
  - Afterhours brief/evidence Re-QA output：`.cao_agent_context/outputs/20260601_185800_22905_stock_qa_code_readonly.answer.txt`，結論 `通過`。
  - `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m py_compile presentation/report.py tests/test_generator_report.py tests/test_market_theme_evidence.py`：passed。
  - `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py tests/test_market_theme_evidence.py`：128 passed，181 warnings。
  - Follow-up `tests/test_generator_report.py`：92 passed，181 warnings。
  - `.qa_tmp/v20_4_21_holding_rr_dry_run_card.json`：`credential_values_included=false`、`schema_change=false`、`data_write=false`、`live_telegram=false`，card 含 `新倉 RR：不適用（既有持倉）`，不含 `數據：RR 2.73`。
  - QA source-error phone-order probe：passed。
  - `git diff --check`：passed。
  - QA 額外反證：按手機閱讀順序掃描三則訊息，禁止詞不出現在 rendered output，資料邊界集中在第三則。
  - 先前 production read-only strategy evidence artifact 仍顯示缺 `classification backtest source-of-truth`，報文正確 fail closed，不回到舊式 `樣本 0｜樣本不足，不判讀`。
- 2356 production read-only artifact：
  - path：`.qa_tmp/production_readonly_2356_positions_events.json`。
  - 安全契約：`credential_values_included=false`、`schema_change=false`、`data_write=false`、`live_telegram=false`。
  - `positions` 摘要：2356 英業達 `shares=0`、`status=CLOSED`、`realized_profit_taken_ratio=0.5`、`last_realized_profit_date=2026-05-25`。
  - `position_events` 摘要：4 筆 sell summary，labels 皆為「賣出」，`second_stage_like_labels=[]`、`has_confirmed_second_stage_label=false`。
  - 解讀：production ledger 目前不是「仍持倉 225」；但也沒有可被報文稱為「已確認第二段停利」的 label。若 Owner 認定實際未賣，需另開 source-of-truth/ledger 稽核任務。
- Runner / 流程修正：
  - `tools/cao_agent/run_qa_code.sh` 已補 QA 啟動前同步主 repo handoff files 到 tech worktree，避免 QA 驗到 stale `CHANGELOG.md`。

## Data / Evidence Status

- production 2026-05 market/theme 資料已回填並通過 read-only audit：
  - `market_theme_confirmed_evidence`：180 rows，20 trade dates，`2026-05-04` 到 `2026-05-29`，duplicate groups 0。
  - `market_theme_index_daily_bars`：200 rows，20 trade dates，`2026-05-04` 到 `2026-05-29`，duplicate groups 0。
  - `sector_theme_members`：12 active mapping rows，只是 mapping，不是 daily history。
  - `daily_signal_snapshot`：每日當時版本留存，不要求舊五月回填為 current version。
- generator 已消費 production `market_theme_confirmed_evidence` history；不是 runtime/local 假資料。

## Next Development

- 重開對話後先以 `git status --branch --short` 與 `tools/cao_agent/check_git_completion_gate.sh` 確認 commit/push 狀態，不再依賴對話記憶。
- 只把 `CHANGELOG.md` 所列 scoped diff 當成本輪驗收範圍；工作樹其他旁支 dirty files 不能因本輪 QA 通過而整包吸收。
- 已處理 Owner 指出的「是 72/100 那個 maturity 到 100%」：目前五維 maturity report 可重跑為 100。
- 已處理本輪「先解合理度跟衝突」的第一層：使用者可見報文不再把無有效進場和推薦感最強同時輸出；raw evidence slot 改成人話，衝突/缺資料保守揭露。
- 已處理 Owner 指出的 v20.4.21 剩餘手機閱讀問題：三日短期背景命名、非加碼 RR、盤後明日語境、卡片資料降噪、第三則資料依據人話化。
- 流程強化不是新增死規則：已新增 `tests/test_generator_report.py` probe，讓同類錯誤可重跑失敗。
- import boundary gate 仍保護後續拆分：presentation 不能反向依賴 writer/DB，core/services 不能依賴 presentation，`core/generator.py` bridge 只是 transitional。
- 另開旁支：若 Owner 認定 2356 英業達實際未賣，查 production positions / position_events 為何目前 artifact 顯示 CLOSED / shares 0。
- 另開旁支：盤點全報文 `追高 / 追蹤` 相關文案。
- 另開旁支：Telegram reply markup 附著最後一則 message 的 delivery consumer 風險。

## Runner Gaps To Fix Later

- CAO auto wrapper QA conclusion parser 已在工作樹修正，待 commit。
- Tech worktree 曾殘留舊 candidate diff；新任務前應自動清理或阻塞並明確提示。
- QA production-read 任務已可用 `CAO_QA_USE_REPO_CONFIG=1` 避免 dummy config；QA sandbox DNS 仍可能失敗，可用 `scripts/smoke_market_theme_evidence_readonly.py --auxiliary-render-artifact-json` 生成 safe read-only artifact。
- QA worktree handoff sync 已補：每次 QA runner 啟動前從主 repo 同步固定 handoff Markdown，避免 stale TASK/CHANGELOG/QA_REPORT 造成反覆 conditional。
- 流程強化：完整報文任務的 QA probe 必須覆蓋 Summary 首屏、卡片、漏斗、交易執行 / 明日計畫，不只驗單一 formatter 或 manifest。
- Git completion gate 已補：repo 落地任務 final 前必須確認 worktree clean、branch 有 upstream、local HEAD 等於 upstream HEAD；標準命令為 `tools/cao_agent/check_git_completion_gate.sh`。
