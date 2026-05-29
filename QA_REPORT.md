# QA_REPORT:

  ## 測試範圍

  - QA 風險預算: L1 / process，符合 TASK.md。本輪不擴大到 full pytest、replay、backfill、loader、writer、RLS、Telegram。
  - 檢查輸入: TASK.md、CHANGELOG.md、git status --short、git diff --stat、git diff -- CHANGELOG.md、SQL contract artifact、handoff verification SQL。
  - 可吸收 diff: CHANGELOG.md 的本輪摘要更新，以及未追蹤但符合本輪目的的 docs/handoff/evidence_phase_4_market_theme_confirmed_evidence_readonly_verification.sql。
  - worktree 殘留: 新增 SQL 目前是 untracked；git diff --stat 不會顯示它，Architect 合併時不能只看 tracked diff 或整包合併。

  ## 風險預算與停止條件

  1. 最值得抓的風險: handoff SQL 是否只讀、無 secret、無 live write。
      - 驗證: keyword/secret 靜態掃描、粗略 statement shape check。
      - 停止條件: 發現 write SQL 或 secret pattern 即 blocked。
  2. 最值得抓的風險: SQL 是否足以讓 Owner/QA 判定 TASK.md 要求的 schema matrix。
      - 驗證: 對照 db/sql/evidence_phase_4_market_theme_confirmed_evidence.sql 的欄位、constraint、index、latest partial index。
      - 停止條件: 缺 hard-contract 欄位/constraint/index 比對項，或可能 false pass，即 conditional / blocked。
  3. 最值得抓的風險: 無 production connection 時是否誤宣告 schema pass。
      - 驗證: 檢查 CHANGELOG.md 與新增 SQL 是否只提供手動只讀 verification，不宣告 production pass。
      - 停止條件: 若宣告 production schema 已通過，即 blocked。

  ## 關聯風險掃描

  - git status --short: CHANGELOG.md modified，新增 SQL untracked。
  - git diff --check -- docs/handoff/... CHANGELOG.md: 通過。
  - 靜態只讀掃描: insert/update/delete/drop/truncate/create/alter/grant/revoke、service_role/token/secret/connection string/postgres://supabase_key 無命中。
  - 粗略 statement check: 16 個 statement，皆為 select 開頭，尾端有分號。
  - 直接消費者補充檢查: Owner/Supabase SQL editor 會看到多個 result sets；未連 production，因此不能產出真正 observed matrix，只能交 Owner 手動執行。

  ## 跨區塊語意一致性

  - TASK.md 要求無安全只讀連線時輸出 read-only SQL，並標記 blocked 或 conditional，不得宣告 schema pass。
  - CHANGELOG.md 與 diff 一致地表示未連 production、不宣告 pass，只新增 handoff SQL。
  - 主要不一致/不足: CHANGELOG.md 宣稱 SQL 覆蓋 allowed values，但新增 SQL 的 freshness/support_level/evidence_status values 只檢查必要值是否出現在 constraint definition，沒有反證額外允許值。因此 production constraint 若
    多允許 experimental，仍可能顯示 pass。
  - 新增 SQL 有 raw check constraints result set，可供人工精確反證，但 summary pass/fail row 本身不足以完成 TASK.md 的「allowed values 與 SQL artifact 一致」硬契約。

  ## 使用者誤讀風險

  - 本輪無 Telegram / summary / dashboard 輸出，手機報文閱讀順序不適用。
  - Owner 可見風險在 Supabase result sets：若 Owner 只看 freshness values = pass、support_level values = pass、evidence_status values = pass，可能誤以為 allowed values 已精確一致；實際上該 SQL 沒有排除額外值。
  - 建議 Architect 吸收時明確提醒: 只能把 raw check constraints 與 SQL artifact 做人工精確比對；不能只依三個 allowed-values pass row 判定 production schema pass。

  ## 質疑與反證

  - 反證「只讀」: 去註解後粗略拆 statement，未發現非 select statement；keyword/secret scan 無命中。
  - 反證「完整 matrix」: 欄位、expected columns、unexpected columns、indexes、latest partial index、comments 都有 result set；但 allowed values pass/fail 非 exact match，存在 false-pass 契約風險。
  - 反證「GitHub fresh run / runtime source-of-truth」: 本輪未新增 runtime cache、loader、writer，也未把 local context 宣告為 production source-of-truth；符合只讀 verification 範圍。
  - 反證「schema artifact intent 被改」: db/sql/evidence_phase_4_market_theme_confirmed_evidence.sql 未出現在本輪 tracked diff；新增 SQL是 verification artifact，不是 migration。

  ## 未測項目

  - 未連 production DB，未驗證 public.market_theme_confirmed_evidence 實際存在或 schema pass。
  - 未跑 PostgreSQL parser validation；本機缺 pglast/psql/Docker/Podman 的狀態已由 Tech 記錄，QA 只做靜態檢查。
  - 未驗證 Supabase SQL editor 實際 result-set 格式。
  - 未測 loader、writer、backfill、RLS、strategy、watchlist、Telegram，符合 TASK 非目標。

  ## QA 結論

  conditional pass

  條件: 本輪可吸收為「提供只讀手動 verification SQL」，但不得宣告 production schema 通過。Owner/Architect 使用結果時，必須人工比對 raw check constraints 是否與 SQL artifact 完全一致，不能只依新增 SQL 的 allowed-values
  pass/fail row；該 row 目前可能漏掉額外允許值。新增 SQL 仍是 untracked，合併時需單獨納入，不可只合併 tracked CHANGELOG.md 或整包 worktree。
