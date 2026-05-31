# QA_REPORT:

  ## 測試範圍

  - 任務尺寸：normal_patch，QA level：L2。
  - 驗證對象：TASK.md、CHANGELOG.md、git diff、correction audit builder、--correction-audit-json fallback、直接相關測試。
  - 可吸收 diff：
      - CHANGELOG.md
      - services/market_theme_evidence_store.py
      - scripts/smoke_market_theme_evidence_readonly.py
      - tests/test_market_theme_evidence_handoff.py
  - worktree 殘留：git status --short 只顯示上述 4 個 tracked 修改；未發現本輪外額外 tracked diff。不得解讀成整包 worktree 可合併，只能吸收上述任務相關 diff。

  ## 風險預算與停止條件

  本輪最值得抓的風險：

  1. daily_signal_snapshot 舊五月 current VERSION 0 rows 被誤當 historical coverage blocker。
      - 驗證：focused pytest 與補充反證案例。
      - 停止條件：history_coverage.conclusion=covered 時不得因 current VERSION 0 rows blocked；blocks_history_coverage=false。
  2. market/theme latest-only / mapping-only 被 daily snapshot 修正誤放行。
      - 驗證：檢查 diff 與測試中 market/theme partial / latest_only / mapping_only 仍導致 status=blocked。
      - 停止條件：read_only_audit_complete 不得出現在 market/theme incomplete 場景。
  3. 使用者誤讀 next_action 為 daily snapshot backfill。
      - 驗證：檢查 blocked_reason、next_action、CLI missing-source fallback。
      - 停止條件：不得輸出 blocked_current_version_snapshot_missing 或 followup_backfill_task_needed 作為本輪 correction audit 指示。

  ## 關聯風險掃描

  - TASK.md / CHANGELOG.md / git diff 一致：修改範圍符合 correction audit 語義修正，未見 DB write、schema、backfill、Telegram、策略 decision 變更。
  - 清理 / 瘦身 / refactor 證據表要求不適用，本輪不是清理任務。
  - 直接消費者：
      - Owner / Architect：可由 daily_signal_snapshot.history_coverage 與 current_version_run_health.blocks_history_coverage=false 判讀。
      - CLI consumer：missing-source fallback 已同步新欄位與 source_error_blocked。
      - QA/test consumer：相關 fixture 已更新。
  - 殘留風險：legacy constants 仍存在於 module，但本輪 correction audit 路徑與 CLI fallback 未再輸出舊 snapshot backfill action；若後續要移除 legacy constant，應另開契約清理任務。

  ## 跨區塊語意一致性

  - blocked_reason 已從 current VERSION 缺五月 rows 改成實際 blocker：daily snapshot 全版本歷史不足或 market/theme historical coverage incomplete。
  - daily_signal_snapshot.current_version_run_health 是 diagnostic，且 blocks_history_coverage=false。
  - daily_signal_snapshot.history_coverage 使用全版本 May rows 判斷 daily-version-as-recorded history。
  - market/theme 三表仍保持 blocker 語義：
      - market_theme_confirmed_evidence latest-only 不放行。
      - market_theme_index_daily_bars latest-only / partial 不放行。
      - sector_theme_members mapping-only 不被當作 May daily history。
  - next_action 指向 market/theme fetch / dedupe 或 source-error，不再要求 daily snapshot current VERSION backfill。

  ## 使用者誤讀風險

  - 本輪不是 Telegram / summary / dashboard 任務，無手機閱讀報文路徑。
  - JSON 閱讀順序檢查：status=blocked、blocked_reason=market/theme...、daily_signal_snapshot.history_coverage=covered、current_version_run_health.diagnostic=current_version_old_month_zero_rows、
    market_theme_historical_coverage latest/mapping blocker、next_action=market_theme...，不會引導 Owner 以為 snapshot 需要 backfill。
  - 尚可能誤讀點：daily_signal_snapshot_may_current_version_coverage.conclusion legacy key 仍可能顯示 no_current_version_may_rows；但同物件新增 diagnostic 與 blocks_history_coverage=false，且新 canonical key 已清楚分流。
    此風險可接受。

  ## 質疑與反證

  已執行：

  - git diff --check：通過。
  - uv run pytest tests/test_market_theme_evidence_handoff.py -k 'correction_audit or may_coverage'：14 passed。
  - uv run pytest tests/test_market_theme_evidence_handoff.py：51 passed。
  - QA 補充反證：market/theme 全部 complete，但 daily_signal_snapshot 全版本歷史缺 1 個 May expected date，current VERSION run-health 仍 blocks_history_coverage=false；結果 status=blocked、blocked_reason 指向
    daily_signal_snapshot May history coverage not covered: partial、無 read_only_audit_complete、無 snapshot/backfill action。通過。

  ## 未測項目

  - 未讀 production DB；本輪不宣告 production market/theme 三表五月資料完整。
  - 未跑 full repo pytest、replay、backfill、live Telegram；依 TASK 的 L2 normal_patch 範圍不需要。
  - 未驗證實際 Supabase credentials CLI live read，避免擴成本輪非目標；CLI missing-source contract 已由測試覆蓋。

  ## QA 結論

  通過
