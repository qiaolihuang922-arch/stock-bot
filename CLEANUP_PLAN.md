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

- 05/31 holiday execution memory bug：
  - 問題：market/theme evidence 已 confirmed，但英業達 2356 因假日只讀當天 events，仍重複建議第二段停利。
  - 結果：已修，QA 通過，推送到 `main`。
  - 抽象教訓：evidence chain 不等於 execution memory；報文決策必須同時消費 production evidence 與 production execution ledger。
- market/theme 2026-05 data backfill：
  - `market_theme_confirmed_evidence` / `market_theme_index_daily_bars` 已有五月歷史並通過 audit。
  - `sector_theme_members` 是 mapping，不當 daily history。
- Markdown 已壓縮為新對話接力版。

## Active Follow-ups

- `next_evidence_chain_development`
  - 目標：把 production market/theme history trend 轉成更清楚的策略輔助說明。
  - 邊界：不放寬買點、不直接改 BUY/SELL、不用假資料。
- `runner_gap: qa_conclusion_parser`
  - 問題：auto wrapper 偶爾把 QA `通過` 判成 failed。
  - 修法方向：只讀 `## QA 結論` 後第一個有效詞：`通過`、`阻塞`、`conditional pass`。
- `runner_gap: tech_worktree_hygiene`
  - 問題：Tech worktree stale diff 會阻塞新任務。
  - 修法方向：新任務前自動檢查、歸檔或要求 Architect 明確處理。
- `runner_gap: production_read_qa_config`
  - 問題：QA dummy Supabase config 會誤判 production read-only audit。
  - 修法方向：允許 safe read-only artifact 或主 repo config。

## Boundaries

- 不刪固定 8 份 Markdown。
- 不清理 production DB rows，除非另有 read-only audit、dry-run、rollback 或 Owner-approved SQL。
- 不把 blocked / conditional candidate diff 當已完成成果吸收。
