# QA_REPORT:

  ## 測試範圍

  本輪 QA 風險預算判斷：risk_patch / L2。最值得抓的風險是：

  1. Owner-facing template/sample 是否真的存在且不會被誤讀為 production confirmed。
  2. allowed payload 是否可 dry-run 產出 JSON / MD / review-only SQL，forbidden runtime 是否 fail closed 且不產 SQL。
  3. no-live-write / no-Telegram / no-version-change 邊界是否被 diff 或文件語意破壞。

  停止條件：只驗證 TASK.md 指定的 approval package workflow、直接消費者與誤讀風險；不擴成 full pytest、replay、backfill、live DB 或 live Telegram。

  已執行：

  - arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence_handoff.py -q：18 passed。
  - allowed sample dry-run：exit 0，產出 .qa_tmp/allowed/approval_package.json、.md、market_theme_confirmed_evidence_2026-05-29.sql。
  - forbidden runtime sample dry-run：exit 2，payload_validation.status=failed、deterministic_sql=null，.qa_tmp/forbidden 無 SQL。
  - git diff --check：通過。
  - 局部 grep no-live-write / secrets pattern：未發現 generator 連線或 live write；命中僅為禁止字串、SQL review text、測試 fake execute()。

  ## 風險預算與停止條件

  本輪沒有理由升級到 full pytest / replay / backfill。驗證停止於：

  - docs/examples 三份 template/sample JSON。
  - handoff docs。
  - generator CLI dry-run 行為。
  - 直接測試檔。
  - diff 是否越過 TASK 禁區。

  ## 關聯風險掃描

  發現一個吸收風險：CHANGELOG.md 宣告新增三份 docs/examples/*market_theme*，檔案在 worktree 存在，但目前是 untracked；git diff --stat 只顯示 CHANGELOG.md、handoff docs、test 三個 tracked diff。若 Architect 只吸收 git
  diff，Owner-facing template/sample 會漏合併，測試也會在乾淨 checkout 失敗。

  可吸收內容必須明確包含：

  - tracked diff：docs/handoff/evidence_chain_market_theme_ops_artifacts.md、tests/test_market_theme_evidence_handoff.py、CHANGELOG.md
  - untracked intended deliverables：docs/examples/market_theme_owner_approved_payload.template.json、docs/examples/market_theme_owner_approved_payload.sample.json、docs/examples/
    market_theme_forbidden_runtime_payload.sample.json

  Worktree 殘留：.qa_tmp/ 是 QA 暫存輸出，未出現在 git status --short，不得合併。

  ## 跨區塊語意一致性

  TASK.md、CHANGELOG.md、docs、sample、generated package 的核心語意一致：

  - allowed source family 包含 owner_approved_persistent。
  - forbidden runtime fail closed。
  - package 標示 mode=non-live-approval-package、write_execution=disabled。
  - SQL header 標示 Agent did not execute this SQL 與不是 production deployment evidence。
  - 未見 scripts/generate_evidence_approval_package.py、core/generator.py、Telegram formatter 或 VERSION diff。

  ## 使用者誤讀風險

  Owner 讀 repo 文件的順序下，handoff docs 開頭已說明 repo-side only、未 live write、非 production ingestion live evidence；template/sample 也標示 not production confirmed、not inserted、not GitHub runner source-of-
  truth。

  剩餘誤讀點：allowed sample 的資料本身使用 evidence_status=confirmed，且 SQL 會生成 insert 語句；目前靠 sample _production_status、docs、SQL header、package write_execution=disabled 抵消誤讀。這可接受，但前提是三份
  untracked sample/template 一起被吸收。

  Telegram 手機閱讀：本輪 TASK 明確不改 Telegram 報文；QA 檢查未見 Telegram formatter / VERSION diff。package 的 post-run checklist 保留 Telegram fail-closed 語意，不會把 sample 變成 Telegram confirmed。

  ## 質疑與反證

  主動反證：

  - 反證「sample 可被當 production」：docs/examples、handoff docs、generated SQL/package 都有 not production / review-only / write disabled 語意。
  - 反證「forbidden runtime 仍產 SQL」：CLI exit 2，deterministic_sql=null，forbidden output dir 無 .sql。
  - 反證「no-live-write 被 generator 破壞」：generator 無 Supabase client / insert/upsert/rpc live call；產出的 insert 僅寫入 review-only SQL file。
  - 反證「乾淨 git diff 可完整交付」：不成立，三份核心 deliverables 目前是 untracked，這是本輪主要條件風險。

  ## 未測項目

  未跑 full pytest、replay、formal backfill、live DB read-only smoke、live Supabase write、live Telegram delivery；這些都在 TASK 非目標或需 Owner 另行批准。未驗證 production rows 是否存在，因本輪只建立 review package
  workflow。

  ## QA 結論

  conditional pass

  條件：Architect 吸收本輪時必須把三份 docs/examples/*market_theme* untracked deliverables 納入可合併 diff；若只用目前 tracked git diff 合併，則本輪應視為阻塞，因 TASK/CHANGELOG 宣告的 template/sample 不會進入 repo。
