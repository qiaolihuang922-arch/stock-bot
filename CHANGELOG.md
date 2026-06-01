# CHANGELOG:

  ## 任務尺寸與風險

  - 任務類型：risk_patch
  - 風險判斷：碰 evidence chain verifier、Telegram evidence 版本、artifact / runner gate 契約；不碰策略門檻、DB schema/write path、live Telegram。

  ## 修改內容

  - 將報文版本升至 v20.4.19。
  - 新增五維 evidence maturity report：
      - data_source_anti_fake
      - telegram_evidence_expression
      - strategy_sample_evidence
      - execution_memory_ledger_evidence
      - repeatable_runner_process
  - 新增 strategy sample read-only artifact / verifier：
      - production read-only artifact 需含 source artifact path/hash proof。
      - missing-source 可被明確揭露且 fail closed。
      - synthetic-only 不得通過 production maturity gate。
  - 新增 positions / position_events / ledger read-only audit artifact / verifier：
      - 揭露 shares/status/event/date/label 摘要。
      - ledger conflict 輸出 unresolved-conflict，且 Telegram 不輸出已確認停利 / 可賣股數 / 有效執行結論。
  - 擴充 scripts/generate_structural_evidence_artifact.py：
      - 保留既有 structural artifact。
      - 新增 --maturity-report 標準命令。
      - blocked case 以 exit code 2 fail closed。
  - 新增 runner/process gate：
      - tools/cao_agent/check_evidence_handoff_gate.sh
      - 檢查 handoff files、maturity artifact、版本、100 分、五維 dimensions、三則 messages、artifacts、source hash、repo/worktree binding、blocking findings 與 read-only safety flags。
  - 新增測試覆蓋：
      - 100 分正例：production all sources、strategy missing-source fail-closed、ledger conflict fail-closed。
      - 負例：synthetic strategy sample、runner stale artifact blocked。
      - 同步既有 v20.4.19 版本預期。

  ## 修改檔案

  - core/generator.py
  - scripts/generate_structural_evidence_artifact.py
  - tools/cao_agent/check_evidence_handoff_gate.sh
  - tests/test_generator_report.py
  - tests/test_market_theme_evidence.py

  ## 最小改動策略

  - 沿用既有 structural evidence artifact / manifest / Telegram evidence renderer。
  - 只在同一 evidence artifact command 上增加 maturity report，不新增策略分支或重寫報文生成流程。
  - runner gate 以獨立 shell verifier 補齊，不改 CAO 主流程語意。
  - 測試只更新相關 evidence / version assertions，未擴成 full repo cleanup。

  ## 契約影響

  - 使用者可見報文版本：v20.4.18 -> v20.4.19。
  - Telegram message order 不變：
      - messages[0] 持倉
      - messages[1] 未持倉 / 非持倉
      - messages[2] short/evidence
      - include_detail=True 時 Details Backup 仍追加最後
  - 新增 public helper：
      - build_evidence_maturity_report(case="production_all_sources_available", now=None)
  - CLI contract 擴充：
      - python scripts/generate_structural_evidence_artifact.py --maturity-report --case production_all_sources_available
      - pass 時 exit 0；synthetic-only / stale runner 等 blocked case exit 2。
  - 新 maturity artifact 輸出包含：
      - maturity_score
      - dimensions
      - blocking_findings
      - artifacts
      - structural_artifact
      - telegram_messages
      - repo_head
      - worktree_status_sha256
      - worktree_diff_sha256
  - Read-only artifact safety flags 維持：
      - schema_change=false
      - data_write=false
      - live_telegram=false
      - credential_values_included=false

  ## 直接消費者同步

  - Owner 手機 Telegram：第三則 evidence 仍呈現 source/status/use/limit/conflict，且 v20.4.19 可見。
  - QA evidence maturity verifier：新增單一標準 maturity report command 與正負 case。
  - Architect / runner：新增 check_evidence_handoff_gate.sh 可檢查 stale / missing artifact。
  - report_context / evidence_manifest consumer：既有 structural coverage helper 未移除，新增 maturity helper 不改既有 manifest key。
  - future production read-only audit consumer：artifact contract 統一為 artifact_id/generated_at/source_type/source_name/source_version_or_query_id/status/use/limit/conflict/records_summary/visible_refs/
    verifier_result。

  ## 未影響模組

  - 未改 DB schema / migration / RLS / grant / policy / role。
  - 未做 production DML、backfill 或 ledger 修復。
  - 未改 production write path。
  - 未執行 live Telegram delivery。
  - 未改買賣策略門檻、持倉狀態機、RR / score / volume 演算法。
  - 未處理 Telegram reply markup 附著最後一則 message 的旁支風險。

  ## 已跑自檢命令

  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m py_compile core/generator.py scripts/generate_structural_evidence_artifact.py：passed
  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python scripts/generate_structural_evidence_artifact.py --maturity-report --case production_all_sources_available：
    maturity_score=100，blocking_findings=[]
  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python scripts/generate_structural_evidence_artifact.py --maturity-report --case strategy_sample_synthetic_only：exit=2，
    strategy_sample_evidence blocked
  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python scripts/generate_structural_evidence_artifact.py --maturity-report --case ledger_position_conflict：maturity_score=100，
    ledger status=unresolved-conflict
  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python scripts/generate_structural_evidence_artifact.py --maturity-report --case runner_stale_artifact_blocked：exit=2，
    repeatable_runner_process blocked
  - tools/cao_agent/check_evidence_handoff_gate.sh . /private/tmp/evidence_maturity_report.json：passed
  - forged minimal 100 artifact：gate blocked
  - artifact with removed production source hash：gate blocked
  - stale repo/worktree binding artifact：gate blocked
  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py tests/test_market_theme_evidence.py：121 passed，169 warnings
  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_strategy_evidence.py tests/test_position_store.py tests/test_cross_day_context.py：21 passed，12
    warnings
  - git diff --check：passed
  - bash -n tools/cao_agent/check_evidence_handoff_gate.sh：passed

  ## 殘留風險

  - Tech 未執行 live Supabase read 或 live Telegram；production online read-only artifact 仍需 QA/Architect 在允許 repo config 的 read-only 環境重跑確認。
  - 新 runner gate 是可重跑 verifier script；Architect final 仍需另外跑 git completion gate。
  - runner_stale_artifact_blocked 已能 fail closed，QA 也反證 forged/stale artifacts 會被 gate 擋下。

  ## 旁支待辦

  - Telegram reply markup 仍附著最後一則 message 的 delivery consumer 風險，另開任務評估。
  - 若 Owner 認定 2356 production ledger 與實際持倉不一致，需另開 source-of-truth 稽核任務；本輪不修資料、不 backfill。
