# CHANGELOG: 交付摘要，移除「未直接編輯 CHANGELOG.md」或等價矛盾句。
  - 明確列出目前需保留的 production source audit 候選 diff:
      - services/market_theme_evidence_store.py
      - scripts/smoke_market_theme_evidence_readonly.py
      - tests/test_market_theme_evidence_handoff.py
  - 明確列出交付文件 diff:
      - CHANGELOG.md
  - 補充 Architect 已在可讀 production 的本機 config fallback 下執行:
      - scripts/smoke_market_theme_evidence_readonly.py --trade-date 2026-05-29 --production-source-audit-json
  - Architect production audit 結果:
      - market_theme_confirmed_evidence rows=0
      - daily_signal_snapshot rows=48
      - signal_runs rows=1
      - signal_items rows=12
      - can_generate_approved_payload=false
      - status=blocked
  - 不宣告 QA 通過；Tech 自檢只代表交付前檢查。

  ## 修改檔案

  - 產品候選 diff:
      - services/market_theme_evidence_store.py
      - scripts/smoke_market_theme_evidence_readonly.py
      - tests/test_market_theme_evidence_handoff.py
  - 交付文件 diff:
      - CHANGELOG.md

  ## 最小改動策略

  - 本次只修正交付摘要，不修改產品代碼、不修改測試、不重構、不清理旁支。
  - 保留目前 production source audit 候選 diff，不因交付摘要修正而擴大或縮小產品範圍。
  - 不改策略方向、不改 Telegram / CLI 使用者報文、不改 DB schema、不改 live write path。
  - 不把 production row count 包裝成 confirmed market/theme evidence；缺 source semantics 時維持 fail closed / blocked。

  ## 契約影響

  - 本次交付摘要修正不改函式回傳結構、message list、payload shape、報文排序、報文分組、DB 寫入或 CLI 輸出契約。
  - 產品候選 diff 的契約重點仍是 read-only production audit / dry-run JSON:
      - write_execution=disabled
      - live_write=false
      - source_family=production_db
      - 缺 market/theme source semantics 時 can_generate_approved_payload=false
      - 缺 source semantics 時 status=blocked
      - 不產生 live write、不 execute approved payload
  - 版本契約: 本輪不改 Telegram / CLI 使用者報文版本；未同步 VERSION 或 Telegram header，因本輪沒有使用者可見報文變更。

  ## 直接消費者同步

  - Architect / Owner: 透過 read-only audit / dry-run output 判斷是否可進入 evidence write approval；本次摘要已補 Architect 實際 production audit 結果。
  - QA: 可依 TASK.md、本 CHANGELOG.md、git diff 與必要局部源碼驗證候選 diff；本摘要明確標示目前 production audit 結果為 blocked，不宣告 QA 通過。
  - 後續 approved payload generator / write CLI: 目前仍不可消費 approved payload，因 can_generate_approved_payload=false 且 approved_payload_preview 應維持 null。
  - 本次未改 public helper、payload、message list 或 formatter，因此沒有新增需同步的產品呼叫方。

  ## 未影響模組

  - 未改策略 decision、watchlist、持倉狀態機或交易建議。
  - 未改 Telegram formatter、header、VERSION、message list contract 或手機閱讀內容。
  - 未改 DB schema、table、column、RLS、grant、policy 或 role。
  - 未執行 live Supabase write、insert、upsert、update、delete。
  - 未執行正式 backfill。
  - 未發 Telegram。
  - 未使用 fake/local/runtime/report-derived/chat data 產生 confirmed evidence。
  - 未把 production row count 提升為 approved market/theme evidence semantics。

  ## 已跑自檢命令

  - sed -n '1,240p' TASK.md: 確認任務為 production DB market/theme evidence source audit 與 approved payload dry-run preview，原任務尺寸為 normal_patch，且要求缺 source semantics 時 blocked。
  - sed -n '1,240p' CHANGELOG.md: 確認既有交付摘要需重寫，避免與 Architect 指令矛盾。
  - git status --short: 確認目前候選產品 diff 僅包含 services/market_theme_evidence_store.py、scripts/smoke_market_theme_evidence_readonly.py、tests/test_market_theme_evidence_handoff.py。
  - git diff --stat: 確認目前候選 diff 為 3 個產品 / 測試檔案，未由本次摘要修正擴大產品 diff。
  - git diff --name-only: 確認候選 diff 檔案清單與本 CHANGELOG 列出的產品候選 diff 一致。
  - Architect 補充執行結果: 在可讀 production 的本機 config fallback 下執行 scripts/smoke_market_theme_evidence_readonly.py --trade-date 2026-05-29 --production-source-audit-json，結果 market_theme_confirmed_evidence
    rows=0、daily_signal_snapshot rows=48、signal_runs rows=1、signal_items rows=12、can_generate_approved_payload=false、status=blocked。

  ## 殘留風險

  - Production DB 目前仍缺可核驗的 market/theme source semantics；daily_signal_snapshot、signal_runs、signal_items 的 row count 只能證明資料存在，不能證明可安全映射為 market_theme_confirmed_evidence approved payload。
  - can_generate_approved_payload=false 代表本輪不能進入 write approval 或 execute；需要 Owner / Architect 後續確認可作為 market_index、sector_theme_key、watchlist_breadth、evidence_value、support_level、lineage 的
    production source semantics。
  - 本次不宣告 QA 通過；QA 仍需依 TASK.md、本摘要與候選 diff 驗證 dry-run 不寫 DB、不使用 forbidden source、不把 runtime/report/chat data 提升為 confirmed。

  ## 旁支待辦

  - 若 Owner 要讓 production rows 轉成 approved payload，需要另開任務定義 source semantics 與 lineage mapping。
  - 若需要正式寫入 market_theme_confirmed_evidence，需另開 write approval / dry-run to execute 任務，且仍不得繞過既有 approval gate。
  - 若 production source 需要新增 schema、view、function、RLS、grant、policy 或 role，需另走 DB schema 變更流程，不納入本輪。
  - 若要擴充其他日期、backfill、Telegram 顯示或完整 ingestion pipeline，需另開任務。
