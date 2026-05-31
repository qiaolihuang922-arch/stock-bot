# CLEANUP_PLAN.md

本文件由 Architect 維護，用來記錄清理、收斂與待補流程。它保存「案例與待辦」，不保存跨任務硬規則。

## Principles

- 固定 8 份 Markdown 不刪，只壓縮內容。
- `AGENTS.md` 只放跨任務原則；事故、版本流水、一次性提醒不長期放入硬規則。
- 新規則先分類再處理：
  - `one_off`：只寫短摘要。
  - `repeated_pattern`：合併既有規則或任務卡契約。
  - `high_risk_invariant`：會造成越權、錯單、live 副作用、版本回退、手機誤讀或資料寫入風險，才升級為硬規則。
  - `runner_gap`：補 runner / agent prompt / worktree gate，不靠文案硬撐。
  - `doc_bloat`：壓縮或刪除過期流水。
- 清理類結論必須有 evidence；不能用「可能有用」作保留理由。

## Completed Compression

- `AGENTS.md` 已從事故堆疊改為角色邊界、交付門檻、DB / runner source-of-truth、報文規則與 post-cycle review 原則。
- `CURRENT_STATE.md` 已改為短上下文，只保留目前產品 / 流程 / blocker / data status。
- CAO agent profiles 已收斂為角色卡、安全邊界與輸出契約，刪除重複口令與舊安全階段描述。
- CAO runner 文件只保留部署、入口、路徑與安全邊界。

## Active Watchlist

- `correction-market-theme-prod-coverage-2026-05`
  - 根因：`delivery_evidence_alignment_gap` + `doc_bloat_risk`。
  - 問題：script / integrity check 通過被誤宣告為 production market/theme 五月資料完成；Owner 截圖只證明部分 latest-source rows，且可能有不同 `as_of` 批次。
  - 已完成：correction audit report 與 CLI 改為 fail-closed；read incomplete / source-error / current VERSION 缺五月 rows 時 `status=blocked`，不輸出 `read_only_audit_complete`。
  - production 現況：`daily_signal_snapshot` 是每日版本留存，不要求舊五月回填為 current version；`market_theme_confirmed_evidence` / `market_theme_index_daily_bars` 只有 `2026-05-29` latest rows；`sector_theme_members` 是 mapping，不是 daily history。
  - 已完成復盤修正：correction audit 已把 current VERSION 舊五月缺 rows 降為 run-health diagnostic；`daily_signal_snapshot.history_coverage` 改依全版本 daily-version-as-recorded 判斷。
  - 已完成 production 資料修復：`market_theme_confirmed_evidence` 180 rows / 20 trade dates / duplicate groups 0；`market_theme_index_daily_bars` 200 rows / 20 trade dates / duplicate groups 0；`sector_theme_members` 維持 mapping-only。
  - 後續：另開 PM 任務讓策略消費 production market/theme history trend；不得把資料完成直接升格為策略已有效使用。
  - 禁止：不得用舊版本 snapshot 或 current-version 缺五月 rows 推導錯誤 backfill 需求；不得把 mapping table 當 daily history。
- CAO QA conclusion parser
  - 根因：`runner_gap`。
  - 問題：auto wrapper 曾把有效 `通過` / `conditional pass` 誤判 failed。
  - 下一步：parser 只讀 `## QA 結論` 或最終結論段第一個有效詞，並讓 conditional pass 條件可由 Architect 明確標記 satisfied。
- CAO production-read QA config
  - 根因：`runner_gap`。
  - 問題：`run_qa_code.sh` 固定 `.qa_tmp/config.py` dummy Supabase，production read-only audit 任務會被誤判 source-error / blocked。
  - 下一步：為 read-only production audit 任務提供安全模式：使用主 repo config 的 read-only key，或由 Architect 產出 audit artifact 讓 QA 反證，不讓 dummy config 覆蓋 production evidence。
- Worktree / agent context hygiene
  - 根因：`runner_gap` + `doc_bloat`。
  - 問題：runtime output、過期 `.cao_agent_context` 與舊 worktree 易造成誤讀。
  - 下一步：流程結束後清理 generated context / outputs，或在新任務啟動時重新生成乾淨 context。

## Cleanup Boundaries

- 不刪固定 8 份 Markdown。
- 不刪未知來源未提交變更。
- 不清理 production DB rows；資料 cleanup 必須先有 read-only audit、dry-run、rollback 或 Owner-approved schema / SQL。
- 不把 blocked / conditional 任務的候選 product diff 當已完成成果吸收。
