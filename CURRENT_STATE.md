# CURRENT_STATE.md

依 `AGENTS.md` 啟動順序閱讀；本文件只保存短上下文與穩定狀態，不重寫啟動清單。

## Stable Context

- 專案：台股策略 Telegram 報文機器人。
- 正式結果以 git / runner 產生報文為準。
- 使用者可見報文版本在 `core/generator.py` 的 `VERSION`，目前已落地為 `v20.4.28`。
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

## Latest Completed Handoff

- task_id：`holdings-risk-list-no-truncation-20260602`
- 狀態：done / QA passed；commit / push 與 Git completion gate 待 final 收口。
- 問題：Owner 指出第三則 `持倉風控檢查` 不應只列前 5 筆再顯示 `另有 N 項持倉風控見詳情`；持倉有幾檔就要列幾檔。
- 修正：
  - `format_holding_control_checklist()` 預設 `limit=None`，使用者可見路徑完整列出全部持倉。
  - 預設不再輸出 `另有 N 項持倉風控見詳情`；顯式 `limit=5` 仍保留 helper 相容性。
  - `holding_control_items()` 沿用輸入 holding order，讓持倉卡、風控檢查、detail index 同序。
- 版本：`core/generator.py` 升為 `v20.4.28`。
- 驗證：QA `通過`；主 repo `tests/test_generator_report.py` 116 passed，225 warnings；`py_compile` passed；`git diff --check` passed。
- QA 反證：6 檔持倉完整列到第 6 筆，不含 `另有` / `見詳情`；card_order == control_order == index_order；未改 strategy decision、RR、DB、未持倉漏斗。
- 流程復盤：第一次 auto 被 stale Tech worktree 擋下；第一次 QA blocked 是 `CHANGELOG.md` stale 成上一輪任務。已保存 residual patch artifact 並同步正確 CHANGELOG 後 Re-QA 通過。這是既有 `runner_gap`，後續仍需修 Tech answer -> main handoff sync。

## Previous Completed Handoff

- task_id：`20260602-risk-codex-fixlist-closeout-4-12`
- 狀態：done / committed / pushed。
- 問題：Owner 要「直接全部完成，不要一直拆」，把 Codex 修復清單剩餘可直接修項第 4/5/6/7/9/12 與第 8/10/11 回歸一次收口。
- 修正：
  - strategy_sample 狀態改以結構化 `structured_status` 判定；legacy 中文文字 summary fail closed，不再靠 grep 反推。
  - market/theme 可靠度由 `evidence_trend` 指標派生，不再硬寫「中等」；strategy sample 資料依據去重。
  - cross_day source status 不足時，不用 previous_state / dedupe_guard 做確認結論。
  - `LAST_OHLCV` fallback payload 帶 `stale / data_date / fallback_source`，報文提示非當日資料。
  - Summary 降噪：同義新倉 / 無有效進場壓縮；空執行區塊、`無新增下單`、`交易執行 0`、全 0 未持倉漏斗不顯示。
  - 持倉排序 / 主行動回歸；已突破負百分比改成人話 `已突破，位於突破區上方`。
- 版本：`core/generator.py` 升為 `v20.4.27`。
- 驗證：QA `通過`；主 repo `tests/test_generator_report.py tests/test_stock_api_history.py` 125 passed，225 warnings；`py_compile` passed；`git diff --check` passed。
- QA 反證：legacy strategy text fail closed、cross_day insufficient 無確認語氣、LAST_OHLCV stale 可見、負突破百分比不出現、全 0 漏斗與 source-missing 空交易區塊不出現。
- 流程復盤：第一輪 QA blocked 是 handoff stale `CHANGELOG.md`；第二、三輪 QA 連續抓到第 10 項殘留（全 0 漏斗、source-missing 空交易區塊）。這是 `runner_gap` + `mobile_reading` + `QA反證`，同類任務必須讓 QA 直接 probe source-missing / 全 0 場景，不能只看一般報文路徑。
- 邊界：未改 strategy decision、RR 公式、DB schema/write path、production DML/backfill、live Telegram；B/C 類仍待研究 / PM 判定。

## Previous Completed Handoff

- task_id：`risk_patch_unheld_funnel_overheat_prepare_fix`
- 狀態：done / committed / pushed。
- commit：`d432545 exclude overheated stocks from prepare funnel`。
- 問題：Owner 清單第 3 項指出過熱 / RR blocker / `過熱降溫` 未持倉仍被漏斗算進 `可準備 / 不可追高觀察 N（不可買）`，卡片、漏斗、summary 容易自相矛盾。
- 修正：`unheld_funnel_state()` 在 `should_show_overheat_rr_blocker(result, holding=False)`、`heat_state HOT/EXTREME` 或 `strong_prepare_bucket == 過熱降溫` 時，不再回傳 `可準備`；改入既有 `等冷卻 / 等回測` 僅追蹤。普通非過熱突破回測仍保留 `可準備`。
- 版本：`core/generator.py` 升為 `v20.4.26`。
- 驗證：QA `通過`；主 repo `tests/test_generator_report.py` 112 passed，221 warnings；`py_compile core/generator.py tests/test_generator_report.py` passed；`git diff --check` passed。QA 補同份報文手機閱讀反證：summary / 漏斗 count / 卡片標題 / 強勢準備同源。
- 邊界：未改 strategy decision、RR 公式 / blocker 定義、DB schema/write、production DML/backfill、live Telegram。

## Earlier Completed Handoff

- task_id：`risk_patch_score_source_status_display_gate_20260602`
- 狀態：done / committed / pushed。
- commit：`ffbaf70 gate score display by evidence status`。
- 問題：Owner 清單第 1 項指出，卡片在 `stock.<name>.score.source_status` 非 available / derived 時仍可能顯示 `S 5/5`、`極強`、`突破確認` 等高置信文字。
- 修正：`presentation/report.py` 新增 score source gate；持倉 / 未持倉卡顯示 S 分數或依賴 score/strength 的高置信盤面文字前讀 `stock.<name>.score.source_status`。score 不足時顯示 `S 證據不足` 或 `S 不可用`，盤面降級為 `強弱證據不足｜待確認`；price / RR / volume 可用時不被誤藏。
- 驗證：QA `通過`；主 repo `tests/test_generator_report.py` 111 passed，221 warnings；`py_compile presentation/report.py tests/test_generator_report.py` passed；`git diff --check` passed。QA 額外反證缺 `stock.TEST.score` manifest 時 fail closed 且不誤傷 price/RR。
- 邊界：未改 strategy decision、RR 公式、DB schema/write、production DML/backfill、live Telegram。

## Older Completed Handoff

- task_id：`evidence_gate_p1_p2_p4_20260602`
- 狀態：done / committed / pushed。
- commit：`9b1e084 fix evidence gate report conflicts`。
- 問題：Owner 指出 evidence_manifest / 資料依據已宣告 strategy_sample、ledger、market/theme 等證據不足或只作背景，但卡片仍顯示 S 5/5、極強、突破確認、精確今日買賣 / 股數 / 均價與可行動 funnel，形成「滿分結論 vs 不足證據」。
- 修正範圍：只處理 P1/P2/P4。
  - P1：strategy_sample missing / insufficient / source-error / unresolved-conflict 時，未持倉高置信行動標籤 fail closed；不再顯示可買、S 5/5、突破確認或進場觸發。
  - P2：持倉卡片 execution 行同時檢查 positions 與 ledger / execution_memory status；任一不足或衝突時，隱藏精確股數、均價、今日買賣，改顯示執行記憶不足。
  - P4：未持倉 funnel source status 納入 strategy_sample；RR 不可用、過熱或證據不足時不得進可買 / 可準備 / 進場觸發。
- 重要反證：strategy_sample source-error 但 price/OHLCV/RR available 時，只阻斷高置信策略樣本依賴結論，不把原因誤寫成 price/OHLCV/RR source failure，也不隱藏可用價格。
- 驗證：QA `通過`；主 repo `tests/test_generator_report.py` 108 passed，221 warnings；`py_compile core/generator.py presentation/report.py tests/test_generator_report.py` passed；`git diff --check` passed。
- 邊界：未改 `services/analysis.py`、strategy decision、RR 公式、DB schema/write、production DML/backfill、live Telegram；P3/P5/P6/P7/P8 未處理。
- 流程復盤：第一輪 QA blocked 是有效攔截，抓到 strategy_sample source-error 被誤歸因為 price/OHLCV/RR failure 且價格被藏掉；第二輪 Tech 先漏 P2，Architect 未送 QA，改用 `CLEAN_TECH_WORKTREE=0` 在候選上補 P2。這是 `QA反證` + `Tech同步` + `runner_gap`，後續同類任務要把 P1/P2/P4 三條 probe 都列為 stop condition，不讓局部通過冒充整輪完成。

## Older Completed Handoff

- task_id：`20260602_intraday_v20_4_24_a1_a2_a3_hard_conflicts`
- 狀態：done / committed / pushed；Git completion gate passed。
- commit：`dab598e fix intraday report hard conflicts`。
- 問題：06/02 盤中 `v20.4.24` 報文有三個手機閱讀硬衝突：未持倉不可買 / 不可追高仍以推薦感 `可準備` 主標籤呈現；同一持倉主行動在卡片 / 決策 / 風控檢查混用；持倉排序在卡片 / 風控檢查 / 詳情索引不一致。
- 修正：報文版本升 `v20.4.25`；不可買未持倉顯示為 `不可追高觀察` / `過熱待回測` / `待回測`；一般續抱持倉可見主行動收斂為 `續抱觀察`；詳情索引的持倉欄位改列 ordered holding names，與持倉卡片和風控檢查同序。
- 驗證：QA `通過`；主 repo `tests/test_generator_report.py` 106 passed，217 warnings；`py_compile` / `git diff --check` passed；QA 額外 rendered-message probe 確認 3 則 message、未持倉 title 無 `可準備 / 可買 / 推薦`、持倉 card/control/index order 一致、同一持倉主行動三處一致。
- 邊界：未改 `services/analysis.py`、strategy decision、RR 計算、holding_status、DB schema/write、live Telegram；降噪第二批未處理，另開。
- 流程復盤：auto runner 第一次被 Tech worktree stale diff 阻塞，已保存 residual patch artifact；Tech agent 前兩次長時間停在分析階段，第三次以「先補紅測再最小實作」指令完成。這是 `runner_gap`，後續需強化 Tech runner 的進度/超時與 worktree hygiene。

## Archived Completed Handoff

- task_id：`fix-bot-workflow-may-backfill-guard-20260602`
- 狀態：done / committed / pushed；Git completion gate passed。
- commit：`c6da0bf skip may backfill in bot workflow`。
- 問題：GitHub Actions `Stock Bot Pro / run-bot` 在 default `run_mode=bot` 時仍跑 May market/theme evidence write，2026-06-02 觸發 `source date outside requested May range` guard 後 exit 1。
- 修正：`.github/workflows/stock-bot.yml` 的 May market/theme evidence backfill step 只在 `backfill_may` / `backfill_and_bot` 執行；default `bot` 明確 skip，不呼叫 `--write --confirm-write`。
- 驗證：QA `通過`；`tests/test_workflow_runtime_config.py tests/test_market_theme_source_backfill.py` 21 passed；QA 補 fake python success path，確認 backfill modes 仍執行且 guard failure 不被吞。
- 邊界：未改 `scripts/backfill_market_theme_sources.py` production guard、DB schema/write、Telegram 報文、live delivery；Node.js 20 deprecation warning 非本輪目標。

## Legacy Completed Handoff

- task_id：`holding-weak-observation-clock-20260601`
- 狀態：done / committed / pushed；Git completion gate passed。當前沒有 Active Tech/QA 任務，實際看板以 `DISPATCH.md` 為準。
- commit：任務二 blocked 文件已在 `9120672 mark support stop task blocked` 推送到 `origin/main`。
- 已完成前置任務：光寶科今日買入盤後不可續買說明已在 `2bd0a48 explain today buy non-current entry` 推送；技嘉過熱 RR 顯示已在 `2036415 show overheat blocker for zero rr` 推送。
- 問題：智原類弱勢遠離持倉只顯示 `續抱觀察 / 降低優先級`，缺觀察第幾天或來源未確認狀態。
- 修正：報文版本升 `v20.4.24`；弱勢遠離且續抱觀察持倉在條件行顯示可信 `弱勢觀察第 N 天`，或缺來源時 fail-closed 顯示 `觀察天數未確認`；`position_events` 非 dict 時不 crash，視為無可信事件。
- 驗證：最終 Re-QA output `.cao_agent_context/outputs/20260601_223651_26823_stock_qa_code_readonly.answer.txt`，結論 `通過`；主 repo related tests passed，Git completion gate passed。
- 邊界：未改 strategy decision、RR 計算、DB write、live Telegram、持倉狀態機。
- 後續：若 Owner 要真正補齊長期第 N 天，需要另開 production source / observation start 資料治理；本輪不 backfill、不新增 schema。
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
