# QA_REPORT:

  ## 測試範圍

  - 本輪為 artifact-only Re-QA，針對前次 scoped code QA 的唯一缺口：`.qa_tmp/production_readonly_2356_positions_events.json`。
  - 任務尺寸 / QA：risk_patch / L2；本輪不擴大成 full pytest、replay、backfill、production write 或 live Telegram。
  - 已讀取：`TASK.md`、`CHANGELOG.md`、`QA_REPORT.md`、`git status --short`、必要 diff、`core/generator.py` message ordering / execution-memory guard、`tests/test_generator_report.py` 06/01 類測試片段、指定 production read-only artifact。
  - 可吸收 diff：`core/generator.py`、`tests/test_generator_report.py`、`tests/test_market_theme_evidence.py`、`CHANGELOG.md`。
  - worktree 殘留旁支：`core/market_theme_evidence.py`、`scripts/smoke_market_theme_evidence_readonly.py`、`services/strategy_evidence.py`、`tests/test_strategy_evidence.py`、`tools/cao_agent/run_auto_dev_cycle.sh`、`tools/cao_agent/run_qa_code.sh`；不得用本輪結論整包吸收。

  ## 風險預算與停止條件

  - 風險 1：artifact 不是 Architect 指定的 production read-only 2356 positions/events 證據。
    - 驗證：檢查 artifact path、artifact_type、status、stock_code。
    - 停止條件：檔案缺失、JSON 無法解析、type/status/stock_code 不符即阻塞。
  - 風險 2：artifact 混入 credential、schema/write/live delivery 行為。
    - 驗證：檢查 credential_values_included、schema_change、data_write、live_telegram。
    - 停止條件：任一安全旗標為 true 或含 credential 值即阻塞。
  - 風險 3：artifact 無法支持 2356 execution-memory source truth 判斷。
    - 驗證：檢查 positions 與 position_events 摘要欄位是否存在且可讀。
    - 停止條件：缺 positions summary 或 events summary/count/date/delta 類摘要，導致無法判讀 production truth 即阻塞。

  ## 關聯風險掃描

  - `TASK.md` / `CHANGELOG.md` / diff：一致。任務為 v20.4.11 risk_patch；`CHANGELOG.md` 列出的 message order、2356 stale guard、噪音壓縮與 diff 中 `core/generator.py` / tests 對齊。
  - `git diff --check`：通過。
  - artifact 解析：通過。
    - artifact_type: `production_readonly_2356_positions_events`
    - status: `ok`
    - credential_values_included: `false`
    - schema_change: `false`
    - data_write: `false`
    - live_telegram: `false`
    - stock_code: `2356`
  - positions 摘要：`positions_rows_count=1`，`position_summary` 顯示 2356 英業達，`shares=0`，`status=CLOSED`，`realized_profit_taken_ratio=0.5`，`last_realized_profit_date=2026-05-25`。
  - events 摘要：`position_events_rows_count=4`，`latest_event_dates=["2026-06-01","2026-05-29","2026-05-28"]`，`sell_events_count=4`，`sell_event_labels` 皆為「賣出」，`recent_sell_deltas=[-225,-112,-75,-138]`，`second_stage_like_labels=[]`，`has_confirmed_second_stage_label=false`。
  - artifact 未輸出 raw credential 或 live delivery 結果；內容是 sanitized summary。

  ## 跨區塊語意一致性

  - `formatTelegramMessages()` 實作順序為 `summary_message -> action_body_message -> evidence_message -> optional details_backup_message`，符合 TASK 的手機閱讀順序。
  - 測試片段覆蓋 06/01 類 message list：Summary 第一則、持倉/未持倉 action body 第二則、Evidence Compact 第三則、Details Backup 最後。
  - 2356 guard 實作要求 second-stage memory 需有「第二」/ SECOND / TP2 label 或至少兩筆 sell deltas；否則 fail closed 為 execution memory 不足，不顯示第二段已執行。
  - production artifact 顯示 2356 positions 目前是 CLOSED 且 shares 0；這與 Owner 原先「看起來尚未賣出」的觀感不同，但正是本輪要求用 production source truth 反證 local/runtime 誤讀的重點。
  - artifact events 有賣出摘要但沒有 confirmed second-stage label；因此報文不得把它說成「已確認第二段停利 event」。

  ## 使用者誤讀風險

  - Artifact 證明本輪可以從 production read-only source 判斷 2356 現況，不再只能依 sanitized fixture 或上週報文推測。
  - 使用者手機閱讀上，若報文仍顯示 2356 尚有持倉或第二段停利已完成，將與 artifact 的 positions CLOSED / shares 0 或 has_confirmed_second_stage_label=false 衝突，應視為下游 report rendering 問題。
  - 本輪 artifact 只證明 production source truth 可讀且安全；不代表已做 live Telegram delivery，也不代表 production DB 有任何寫入。

  ## 質疑與反證

  - 反證 1：若 artifact 是缺失或 stale，本輪只能維持 conditional pass。結果：指定 path 存在，JSON 可解析，`generated_at=2026-06-01T03:37:47.390344Z`，狀態 ok。
  - 反證 2：若 artifact 需要 credential 或 production write 才取得，不可吸收。結果：`credential_values_included=false`、`data_write=false`、`schema_change=false`、`live_telegram=false`。
  - 反證 3：若 artifact 只列安全旗標、不含 2356 positions/events 摘要，不能關閉前次 QA 缺口。結果：positions 有 row count 與 summary；events 有 row count、latest dates、sell count、labels、second-stage label 判定與 sell deltas。
  - 反證 4：Owner 原誤讀路徑是「看起來仍持倉」。結果：artifact 顯示 production positions 為 CLOSED、shares=0，可作為下游報文 source truth 反證。

  ## 未測項目

  - 未重跑 full pytest；artifact-only Re-QA 不需要擴大。
  - 未重跑 replay / backfill。
  - 未做 production write、schema change 或 live Telegram delivery。
  - 未驗收旁支 dirty files 是否可合併。
  - 未直接查 production DB；本輪只驗 Architect 提供的 sanitized read-only artifact。

  ## QA 結論

  通過

  前次 conditional pass 的缺口已由 `.qa_tmp/production_readonly_2356_positions_events.json` 補齊。Artifact schema/content 符合 Architect 指定安全契約，且提供 2356 positions/events production source truth 摘要；本輪可將 scoped code QA 從 conditional pass 收斂為通過。現有 tracked dirty files 仍需按可吸收 diff 與旁支殘留分開處理，不得整包合併。
