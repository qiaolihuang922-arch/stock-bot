# QA_REPORT:

  ## 測試範圍

  本輪判定為 risk_patch / QA L2。驗證聚焦 DB write path 介面契約、fail-closed、mock execute payload、文件邊界與可吸收 diff；未擴大到 full pytest、replay、backfill、production Supabase write、RLS/grant 或 Telegram 實際報
  文。

  已讀取：

  - TASK.md
  - CHANGELOG.md
  - git status --short
  - git diff --stat
  - git diff 相關檔案
  - services/market_theme_evidence_store.py
  - scripts/write_market_theme_confirmed_evidence.py
  - tests/test_market_theme_evidence_handoff.py
  - docs/examples/*market_theme*payload*.json
  - docs/handoff/evidence_chain_market_theme_ops_artifacts.md
  - 既有 schema artifact db/sql/evidence_phase_4_market_theme_confirmed_evidence.sql

  已執行：

  - git diff --check：passed
  - TMPDIR=.qa_tmp PYTHONPATH=.qa_tmp:. .venv/bin/python -m pytest tests/test_market_theme_evidence_handoff.py -q：22 passed
  - allowed sample dry-run CLI：exit 0，write_execution=disabled，rows_to_upsert=1
  - forbidden runtime payload dry-run CLI：exit 2，payload_validation.status=failed，execute_payload=null
  - --execute 缺 env：exit 2，列出 SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY，rows_written=0
  - QA 額外 mixed source fixture：exit 2，reason=forbidden source_family
  - QA 額外 missing source fixture：exit 2，reason=missing source_family

  ## 風險預算與停止條件

  本輪最值得抓的風險：

  1. DB write path 被 sample / runtime / mixed source 洗成 confirmed production rows。
     驗證：forbidden runtime、mixed allowed+runtime、missing source 都 exit 2，且不產生 execute payload。
     停止條件：確認 fail-closed 與 rows_to_upsert=0，不延伸 production write。
  2. CLI 預設或缺 env 時誤寫 DB / 洩漏 secret / 要 Owner 手動跑普通 DML。
     驗證：預設 dry-run 不寫、缺 env execute blocked，只輸出 env 名稱不輸出值；docs 說非 schema evidence row 走 repo script / approved API。
     停止條件：確認 write_execution=disabled/blocked 與 rows_written=0，不測真 service role。
  3. 實作與 table contract / 可合併 diff 不一致。
     驗證：schema artifact 欄位與 conflict target 對上 helper WRITE_COLUMNS / UPSERT_CONFLICT_TARGET；檢查 status 發現 CLI script 是 untracked。
     停止條件：確認 tracked diff 未改 schema/Telegram/VERSION；標出 untracked script 必須納入吸收，不建議整包合併。

  ## 關聯風險掃描

  TASK.md、CHANGELOG.md 與實作大方向一致：新增 repo-side write CLI、預設 dry-run、缺 env fail-closed、fake client execute test、文件更新，未改 DB schema / Telegram formatter / core/generator.py VERSION。

  可吸收 diff 應只包含本輪相關內容：

  - tracked：services/market_theme_evidence_store.py
  - tracked：tests/test_market_theme_evidence_handoff.py
  - tracked：docs/examples/market_theme_owner_approved_payload.sample.json
  - tracked：docs/examples/market_theme_owner_approved_payload.template.json
  - tracked：docs/handoff/evidence_chain_market_theme_ops_artifacts.md
  - untracked but required：scripts/write_market_theme_confirmed_evidence.py
  - delivery doc：CHANGELOG.md

  不可把 worktree 整包視為可吸收。scripts/write_market_theme_confirmed_evidence.py 目前是 untracked；若 Architect 只套用 git diff 的 tracked patch，CLI 會缺檔，測試 import 也會失敗。因此結論不能是無條件通過，只能
  conditional pass：吸收時必須明確納入該 untracked script，並排除 .qa_tmp/ 測試暫存。

  未發現 schema SQL、RLS/grant/policy/role、Telegram formatter、策略 decision 或 core/generator.py VERSION 被本輪 diff 修改。

  ## 跨區塊語意一致性

  CLI、docs、tests 對以下語意一致：

  - target table：public.market_theme_confirmed_evidence
  - conflict target：trade_date,market_index,sector_theme_key,source_family,source_name,as_of
  - dry-run 預設不寫 DB，輸出 write_execution=disabled
  - --execute 需明確 flag 與 SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY
  - forbidden / missing / mixed source fail closed
  - 本輪不做 live Telegram、不改策略 decision、不改 VERSION

  一個文件語意殘留需 Architect 注意但不阻塞本輪：template 仍有「Owner runs read-only verification after any manual SQL execution」，這是在 schema/manual SQL 舊邊界下可理解，但新流程主文已補「non-schema evidence row
  writes 使用 repo CLI / approved API」。目前不會直接引導 Owner 對本輪普通 DML 手動執行。

  ## 使用者誤讀風險

  本輪沒有 Telegram / summary / dashboard 輸出變更，手機閱讀順序檢查適用於 CLI/operator 可見輸出：

  1. Owner/operator 先看到 mode、target_table、write_execution。
  2. dry-run 顯示 disabled、row count 與 sanitized preview，不像已寫入。
  3. execute 缺 env 顯示 blocked 與 missing env names，沒有 secret 值。
  4. docs 明確說 dry-run/fake-client test 不是 production rows 已寫入，也不是 GitHub fresh runner 已消費。

  未發現會讓 Owner 誤判「已完成 production write」、「Telegram 已消費新 rows」或「需要手動跑普通 DML」的主要輸出問題。

  ## 質疑與反證

  主動反證 Tech 未完全覆蓋的路徑：

  - mixed allowed + forbidden source：QA 自建 .qa_tmp/qa_mixed_source_payload.json，top-level owner_approved_persistent 但 row-level runtime，CLI exit 2，reason=forbidden source_family，未產生 rows。
  - missing source：QA 自建 .qa_tmp/qa_missing_source_payload.json，CLI exit 2，reason=missing source_family。
  - direct consumer contract：核對既有 schema artifact，write columns 未包含 id/created_at/updated_at，conflict target 對上 unique index。
  - GitHub fresh runner source-of-truth：本輪只新增 write interface；read-only loader 未改，仍不消費 local/runtime/template/sample artifact。未驗證 live runner，符合 TASK 非目標。

  反證結果可接受，但吸收條件是 untracked CLI script 必須一起納入。

  ## 未測項目

  - 未執行 production --execute。
  - 未驗證真 Supabase service role write。
  - 未跑 full pytest。
  - 未跑 replay/backfill。
  - 未驗證 production RLS/grant/policy/role。
  - 未驗證 GitHub runner read-only consumption。
  - 未驗證 Telegram confirmed evidence 實際報文。

  以上皆符合 TASK 非目標與 L2 範圍。

  ## QA 結論

  conditional pass

  條件：Architect 吸收 diff 時必須明確納入 untracked scripts/write_market_theme_confirmed_evidence.py，不能只套用 tracked git diff；同時排除 .qa_tmp/ 測試暫存與其他 worktree 殘留。若漏掉該 untracked script，本輪 CLI
  contract 與測試都不成立，應視為 blocked。
