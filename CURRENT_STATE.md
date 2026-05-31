# CURRENT_STATE.md

本文件由 Architect 維護，保存新會話需要的短上下文。新會話先讀 `AGENTS.md`、`DISPATCH.md`，再讀本文件。

## Project Snapshot

- 專案：台股策略報文機器人。
- 正式交付：git / runner 產生 Telegram 報文。
- 股票清單來源：`core/watchlist.py`。
- 使用者可見 Telegram 版本以 `core/generator.py` 的 `VERSION` 為準。
- 最新 pushed commit 以 `git log -1` 為準。
- 固定 8 份 Markdown 不刪：`AGENTS.md`、`DISPATCH.md`、`RESEARCH.md`、`CURRENT_STATE.md`、`CLEANUP_PLAN.md`、`TASK.md`、`CHANGELOG.md`、`QA_REPORT.md`。

## Process State

- Architect 是唯一總控入口；產品 / 顯示 / 策略 / feature 任務預設 PM -> Tech -> QA。
- Owner 的「開始 / 繼續 / 修復 / 檢查 / 清理 / 直接來」只啟動流程，不是越權授權。
- Architect 可直接處理流程文件、規則壓縮、狀態收斂；不得順手改產品代碼。
- Post-cycle review 必須做抽象治理：規則留原則，事故留摘要，避免 `AGENTS.md` 膨脹。
- 完成結論必須和 Owner 目標同口徑；局部工具通過不得升格為整體完成。

## CAO Runtime

- CAO API：`http://127.0.0.1:9889/`
- CAO UI：`http://127.0.0.1:5173/`
- 確認 / 啟動：`tools/cao_agent/ensure_cao_services.sh`
- 部署：`tools/cao_agent/DEPLOYMENT.md`
- Agent profile 模板：`tools/cao_agent/profiles/stock_*.md.template`
- 分配或回覆前端地址前，先確認 API 與 UI 正在 listen；未啟動就先啟動。

## Stable Product Contracts

- 正式 runner 視為無狀態；跨日狀態、已執行事件、歷史證據必須來自 production DB 或 Owner 指定持久來源。
- DB schema / RLS / grant / policy / role / index / constraint 變更需要 Owner 先審 SQL。
- 非 schema data write / backfill 走 repo script 或 service API，不要求 Owner 手寫 DML。
- local / runtime / worktree / agent 對話只能作同 run 輔助，不能當 production history。
- 缺資料、source-error 或可信度不足時 fail closed，不用假資料補成 confirmed。

## Current Result

- task_id：`correction-market-theme-prod-coverage-2026-05`
- 狀態：market/theme 2026-05 historical fetch 與 confirmed evidence dedupe 已完成。
- 問題：先前把 script / integrity check 通過誤當成 production market/theme 五月 coverage 完成；Owner 截圖顯示主要是 `2026-05-29` latest-source rows，且可能有不同 `as_of` 批次。
- 已修 correction path：`--correction-audit-json` 可重跑，source-error / missing-source / read incomplete / current VERSION 缺五月 rows 會 `blocked`，不再誤給 `read_only_audit_complete`。
- 已修 snapshot 語義：`daily_signal_snapshot` 的歷史設計是每日當時版本留存；current VERSION 舊五月 0 rows 只作 run-health diagnostic，不作歷史 coverage blocker。
- 已用 repo script 寫入 production：`market_theme_confirmed_evidence` 180 rows、`market_theme_index_daily_bars` 200 rows，均為 20 trade dates，duplicate groups 0。
- 下一步可以推進證據鏈功能擴張，但要先讓策略實際消費 production `market_theme_confirmed_evidence` history trend。

## Data / Evidence Status

- production read-only audit on 2026-05-31：
  - `daily_price`：240 rows，20 trading days，12 stocks，date range `2026-05-04` to `2026-05-29`，無 business-key duplicates。
  - `daily_signal_snapshot`：按每日當時版本留存，不要求舊五月回填為 current version；全版本 936 rows / 20 trading days，`history_coverage.conclusion=covered`；current `v20.4.6` 有 0 May rows 只作診斷，`blocks_history_coverage=false`。
  - `market_theme_confirmed_evidence`：180 rows，20 trade dates，date range `2026-05-04` to `2026-05-29`，source `market_data:twse_openapi_mi_index`，`latest_source_only=false`，duplicate business-key groups 0。
  - `market_theme_index_daily_bars`：200 rows，20 trade dates，date range `2026-05-04` to `2026-05-29`，source `market_data:twse_openapi_mi_index`，`latest_source_only=false`，duplicate business-key groups 0。
  - `sector_theme_members`：12 active mapping rows，valid_from `2026-01-01`，source `market_data:twse_openapi_t187ap03_L`；這是 mapping，不是五月 daily history。
- 獨立 audit 命令：`PYTHONPATH=. arch -arm64 .venv/bin/python scripts/smoke_market_theme_evidence_readonly.py --correction-audit-json --limit 20000`，結果 `status=pass` / `read_only_audit_complete`。
- production trend consumption check：`fresh_runner_rebuild=passed`；`core.generator.market_theme_summary_evidence` 已消費 production `market_theme_confirmed_evidence` history，`observed_days=8`、`recent_supporting_days=3`、`support_streak_days=8`；未使用 daily_signal_snapshot / runtime / local cache 作 market/theme evidence。
- full integrity check：production DB readonly passed、May data available passed、dry-run report generated passed、summary/cards/checklist/funnel/version consistency 全部 passed，blocked_reasons 空。
- full pytest：261 passed，warnings 153（第三方 pyiceberg / supabase / Python 3.9 deprecation 類警告）。
- 證據鏈下一步：把 production history trend 轉成更明確的策略提示 / 題材證據呈現，而不是只證明資料表存在。

## Validation Baseline

- 報文 / formatter 類：至少檢查手機閱讀順序、版本 header、跨區塊語意、漏斗與詳情一致。
- DB / evidence 類：至少檢查 source-of-truth、fail-closed、read-after-write 或 read-only audit、consumer 是否真的使用 production source。
- Runner 類：以 fresh runner / git path 為準；本地成功只算輔助證據。

## Known Runner Gaps

- CAO auto wrapper 曾多次誤判 QA `通過` / `conditional pass`；需修 QA conclusion parser。
- CAO QA runner 固定 dummy Supabase config，會讓 production read-only audit 類任務誤 blocked；需允許使用主 repo config 或注入 Architect 產出的 audit artifact。
- Worktree / runtime output 容易留下舊上下文；任務結束後應清理或重新生成 agent context。
- Agent 規則已收斂為角色卡與安全邊界；具體事故不得再硬塞進 profile。
