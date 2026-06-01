# CLEANUP_PLAN.md

保存待補流程與高信號事故摘要；不保存長篇流水，不把單次事故塞進 `AGENTS.md`。

## Governance

- `AGENTS.md` 只放跨任務原則。
- 具體事故進本文件或 `CURRENT_STATE.md`，並定期壓縮。
- 規則變更先分類：
  - `one_off`：只記摘要。
  - `repeated_pattern`：合併既有規則或任務卡契約。
  - `high_risk_invariant`：才升級到硬規則。
  - `runner_gap`：補 runner / agent prompt / worktree gate。
  - `doc_bloat`：壓縮或刪除過期流水。

## Completed

- `intraday_20260601_report_sequence_execution_memory_noise_v20_4_11`：
  - 問題：Owner 貼出 2026-06-01 盤中完整報文，指出主體/詳情順序不符合手機閱讀、英業達 2356 第二段停利仍像沿用上週操作、報文 source/backtest/detail 噪音過多。
  - 結果：PM -> Tech -> QA 完成，QA `通過`；主 repo 工作樹已吸收 scoped diff，未 commit / 未 push。
  - 關鍵修正：`formatTelegramMessages()` 固定 Summary -> action body -> Evidence Compact -> optional Details Backup；2356 second-stage execution memory 未確認時 fail closed；verbose source/backtest/detail 移到 compact evidence / details backup；`evidence_manifest` 補 execution_memory。
  - Production 反證：`.qa_tmp/production_readonly_2356_positions_events.json` 顯示 2356 production `positions` 為 `shares=0 / CLOSED`，`position_events` 有 sell summary 但無 second-stage-like labels。報文不得把一般賣出事件講成「已確認第二段停利」；若 Owner 認定未賣，需另查 ledger source truth。
  - 規則治理：`repeated_pattern` + `evidence_chain` + `mobile_reading` + `runner_gap`。完整報文問題不得切片驗收；QA artifact 必須在 QA worktree 可見，否則會造成假 conditional。
  - 流程優化：Architect 生成 safe read-only artifact 後，需同步到 QA 實際 worktree 或改 runner 標準 artifact path，避免「主 repo 有、QA 看不到」的缺檔反覆。
  - 邊界：不改 DB schema/write/live delivery；不校正 production ledger；旁支 dirty files 不得用本輪結論整包吸收。
- `unified_report_db_source_manifest_v20_4_10`：
  - 問題：Owner 指出完整 Telegram 報文被切成片段理解，且使用者可見資料沒有明確連回 DB / source-of-truth；缺 source 的 BUY-like 候選仍可能在 Summary 看起來像推薦。
  - 結果：PM -> Tech -> QA 反覆到 QA `通過`；主 repo 工作樹已吸收 scoped diff，未 commit / 未 push。
  - 關鍵修正：Summary first；新增共用 `report_context / evidence_manifest`；price/OHLCV/RR source 不足時 Summary、漏斗、交易執行 / 明日計畫、未持倉卡一致 fail closed；`🔥 最強` 不再顯示 source-ineligible candidate 的排序 / 評級；混合 source-valid / source-ineligible 候選不互相污染。
  - QA 反證：盤中與盤後完整報文 probe passed；source-ineligible BUY-like candidate 不出現可買、交易執行、明日計畫、最強候選、排序分或評級分；runtime/local 缺源卡片不顯示精確 RR / S / V / 價格。
  - 規則治理：`repeated_pattern` + `evidence_chain`。不可只做 manifest 或卡片 source line；必須驗完整手機閱讀順序與所有直接消費者。
  - 流程優化：完整報文任務的 QA 應固定補一個 Tech 未覆蓋的首屏 Summary 反證，且至少包含「有效來源候選 + 缺源高分候選」混合情境，防止 source gate 停在局部 formatter。
  - 邊界：不改 DB schema/write/live delivery；旁支 dirty files 不得用本輪結論整包吸收。
- `fix_strategy_sample_evidence_consumption_v20_4_8`：
  - 問題：報文 `策略證據 v20.0` 仍顯示 `樣本 0 / 樣本不足`，手機閱讀上像 strategy evidence 有被使用但沒有提供有效結論。
  - 結果：已由 PM -> Tech -> QA 完成並吸收到工作樹；QA `通過`，未 commit / 未 push。
  - 邊界：未做 live Telegram / DB write / schema；production read-only dry-run 已驗證 v20.4.9 會 fail closed。
  - Production 現況：缺 `classification backtest source-of-truth`，所以正確結論是 strategy sample 層不可用，不是可買 / 不可買決策依據。
  - 抽象教訓：證據鏈不能只「有區塊」；每一層要有狀態、source、不可用原因與對 stock decision 的作用邊界。
- `runner_gap: qa_handoff_sync`：
  - 問題：QA runner 使用可重用 tech worktree，但啟動前未同步主 repo handoff files，導致主 repo 已更正 `CHANGELOG.md` 後，QA 仍讀到 worktree stale 內容並反覆 conditional。
  - 結果：`tools/cao_agent/run_qa_code.sh` 已在 QA 啟動前同步固定 handoff Markdown。
  - 分類：`runner_gap`。
  - 抽象教訓：重跑流程前先消除 runner 的 stale-input 來源；不能靠下一輪 agent 記住上輪錯誤。
- `next_evidence_chain_development_market_theme_auxiliary_layer`：
  - 問題：production market/theme evidence 已 confirmed，但報文缺少手機可讀的策略輔助層，容易讓 Owner 無法分辨背景支持、strategy sample、個股買點/風控。
  - 結果：已由 PM -> Tech -> QA 完成並吸收到工作樹；QA `通過`，未 commit / 未 push。
  - 邊界：未做 live Telegram / DB write / schema；production positive rendering 由 safe read-only artifact 反證。
  - 抽象教訓：confirmed evidence 必須在報文中降格為背景輔助，不得升格成 BUY 或追高提示。
- `runner_gap: qa_conclusion_parser`：
  - 問題：auto wrapper 用 `\b` 解析中文 `QA 結論` 標題，導致有效 `conditional pass` 被判 failed。
  - 結果：工作樹已修 parser regex，改抓 `QA 結論` 行尾或冒號。
  - 分類：`runner_gap`。
- 05/31 holiday execution memory bug：
  - 問題：market/theme evidence 已 confirmed，但英業達 2356 因假日只讀當天 events，仍重複建議第二段停利。
  - 結果：已修，QA 通過，推送到 `main`。
  - 抽象教訓：evidence chain 不等於 execution memory；報文決策必須同時消費 production evidence 與 production execution ledger。
- market/theme 2026-05 data backfill：
  - `market_theme_confirmed_evidence` / `market_theme_index_daily_bars` 已有五月歷史並通過 audit。
  - `sector_theme_members` 是 mapping，不當 daily history。
- Markdown 已壓縮為新對話接力版。

## Active Follow-ups

- `runner_gap: tech_worktree_hygiene`
  - 問題：Tech worktree stale diff 會阻塞新任務。
  - 修法方向：新任務前自動檢查、歸檔或要求 Architect 明確處理。
- `runner_gap: production_read_qa_config`
  - 問題：QA dummy Supabase config 會誤判 production read-only audit；即使允許 repo config，QA sandbox 仍可能因 DNS/network 回 source-error。
  - 已做：`run_qa_code.sh` 新增 `CAO_QA_USE_REPO_CONFIG=1`，並在 read-only QA 模式臨時覆蓋 ignored worktree `config.py`，跑完恢復。
  - 已做：`scripts/smoke_market_theme_evidence_readonly.py --auxiliary-render-artifact-json` 產生標準 safe read-only artifact，避免 Architect 手動片段。
  - 已驗：safe read-only artifact 可讓 QA 驗證 production positive rendering 並給 `通過`。
- `runner_gap: strategy_evidence_readonly_artifact`
  - 問題：本輪 strategy evidence production read-only 只能用 inline smoke；QA sandbox DNS 失敗時只能核對 Architect sanitized evidence。
  - 修法方向：補 `scripts/smoke_strategy_evidence_readonly.py` 或擴充現有 smoke CLI，輸出無 credential、無 write/live 的標準 artifact，欄位至少含 version、production_readonly、source_status、has_old_sample0_style、summary_preview。
- `runner_gap: qa_artifact_sync`
  - 問題：Architect 在主 repo 生成 `.qa_tmp/production_readonly_2356_positions_events.json`，但 QA runner 在 tech worktree 執行，第一次 Re-QA 因 artifact 不存在而 conditional。
  - 已做：本輪手動同步 artifact 到 `/Users/liveroom/stock-bot-agent-worktrees/tech_write/.qa_tmp/` 後 artifact-only Re-QA 通過。
  - 修法方向：runner 接受 artifact path 時自動同步到 agent worktree，或統一將 safe read-only artifacts 寫入 shared `.cao_agent_context/artifacts/` 並由 QA 固定讀取。

## Boundaries

- 不刪固定 8 份 Markdown。
- 不清理 production DB rows，除非另有 read-only audit、dry-run、rollback 或 Owner-approved SQL。
- 不把 blocked / conditional candidate diff 當已完成成果吸收。
