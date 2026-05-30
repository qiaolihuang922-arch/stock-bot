# QA_REPORT:

  ## 測試範圍

  本輪任務尺寸：risk_patch，QA level：L2+。驗證聚焦 repo-side non-live approval package，不擴大到 full pytest、正式 backfill、live DB、live Telegram。

  已檢查：

  - TASK.md
  - CHANGELOG.md
  - git status --short
  - tracked diff：CHANGELOG.md、docs/handoff/evidence_chain_market_theme_ops_artifacts.md、tests/test_market_theme_evidence_handoff.py
  - untracked but required task artifact：scripts/generate_evidence_approval_package.py
  - 直接依賴：services/market_theme_evidence_store.py

  已跑命令：

  - pytest tests/test_market_theme_evidence_handoff.py tests/test_market_theme_evidence.py -q：36 passed, 17 warnings
  - git diff --check -- docs/handoff/evidence_chain_market_theme_ops_artifacts.md tests/test_market_theme_evidence_handoff.py CHANGELOG.md：通過
  - 靜態掃描 generator：未發現 create_client、insert/upsert/rpc/execute、Telegram 發送或外部請求入口
  - QA 補充負面檢查：fixture-derived fail closed、secret-like postgres:// payload 不產生 SQL、allowed package 明確標示 manual approval / not executed：通過

  ## 風險預算與停止條件

  本輪最值得抓的風險：

  1. approval package 被誤讀成已寫入 production。
      - 驗證：檢查 package / SQL header / docs / not_executed wording。
      - 結果：SQL header 含 Owner manual approval required、Agent did not execute this SQL、not evidence of production deployment；package 列出 live write / backfill / RLS / Telegram 未執行。
  2. forbidden / fake / runtime source 仍產生 deterministic SQL。
      - 驗證：Tech 測試覆蓋 forbidden、mixed source；QA 額外補 fixture-derived。
      - 結果：fail closed，deterministic_sql is None。
  3. generator 產生 live side effect。
      - 驗證：讀 generator，掃描 Supabase client、DB write、Telegram、外部請求、SQL execute pattern。
      - 結果：未發現 live write / live delivery pattern；只讀 JSON、build package、可選寫本地 artifacts。

  停止條件已達成：package contract、source guard、SQL determinism、no-live-write pattern、read-only smoke fail-closed 相關局部測試均已覆蓋；未擴大到 TASK 禁止的 live 驗證。

  ## 關聯風險掃描

  TASK.md、CHANGELOG.md 與 worktree diff 大致一致。需注意 scripts/generate_evidence_approval_package.py 是 untracked，git diff --stat 不會顯示；但它是本輪核心 artifact，屬於可吸收 diff 的必要部分。

  可吸收範圍：

  - scripts/generate_evidence_approval_package.py
  - docs/handoff/evidence_chain_market_theme_ops_artifacts.md
  - tests/test_market_theme_evidence_handoff.py
  - CHANGELOG.md

  worktree 殘留：

  - .qa_tmp/config.py 為測試暫存/環境產物，不屬於可吸收產品 diff。
  - 不建議整包合併 worktree，只吸收上述任務相關檔案。

  清理 / 瘦身 / refactor 證據表要求：本輪不是清理任務，不適用。

  ## 跨區塊語意一致性

  Package、docs、CHANGELOG 對本輪邊界一致：

  - schema_decision=no-schema-change
  - mode=non-live-approval-package
  - write_execution=disabled
  - 不做 live Supabase write
  - 不做 formal backfill
  - 不改 RLS / grant / policy / role
  - 不改 Telegram formatter / VERSION
  - package 不代表 production deployment

  read-only smoke fail-closed 沒被本輪改動回退；局部測試仍覆蓋缺 env / 無 rows / 不合格 rows 不會讓 telegram_confirmed=true。

  ## 使用者誤讀風險

  Owner 可見 artifact 的手機 Telegram 報文本輪不變；本輪主要使用者可見面是 approval package / docs / SQL。

  誤讀路徑檢查：

  - SQL header 明確說 agent 沒執行。
  - package manual_approval_required 明確列出 Owner review、另行批准 SQL、執行後 read-only verification。
  - not_executed 明確列出 live write、formal backfill、RLS/grant/policy/role changes、Telegram delivery。
  - docs 說明 package 只是 review artifacts，不是 production ingestion live evidence。

  未發現會讓 Owner 誤判「已入庫」「已上線」「Telegram 已 confirmed」的文案。

  ## 質疑與反證

  QA 補充 Tech 未覆蓋的反證：

  - fixture-derived 不是 Tech 測試清單中的精確值，但仍因非 approved persistent source fail closed，不產生 SQL。
  - payload 內含 postgres:// secret-like marker 時，即使 source allowed，也會讓 validation failed 並清空 SQL。
  - 靜態掃描 generator 沒有 Supabase client、DB execute、insert/upsert/rpc、Telegram delivery 或外部 request pattern。

  對直接消費者：

  - Owner / manual operator：package 與 SQL header 足以看出需要人工批准。
  - QA / Architect：JSON package 欄位可驗證，CLI 有 exit code 區分 passed / failed。
  - GitHub fresh runner / Telegram：未改 consumption；package 本身不會讓 confirmed 成立。

  ## 未測項目

  - 未做 production DB live verification，符合 TASK 禁止事項。
  - 未執行 production SQL、formal backfill、RLS/grant/policy/role 變更。
  - 未做 live Telegram delivery 或完整 Telegram 長報文驗證，因本輪未改 Telegram 報文。
  - 未跑 full pytest，符合本輪 L2+ 停止條件與 TASK 禁止擴大範圍。

  ## QA 結論

  通過
