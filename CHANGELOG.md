# CHANGELOG: v20.4.18 structural evidence coverage 100%

  ## 任務尺寸與風險

  - task_id: evidence-chain-structural-coverage-100
  - 任務類型: risk_patch
  - Tech 結論: implemented
  - 阻塞狀態: none

  ## 修改內容

  - 將 Telegram 報文版本升至 v20.4.18。
  - 在 report_context["evidence_manifest"] 補齊 structural evidence slot 欄位：
      - layer
      - target
      - source
      - status
      - use
      - limit
      - conflict
      - visible_refs
  - 補齊必要 evidence layers：
      - market-theme
      - strategy-sample
      - positions
      - ledger
      - price-ohlcv
      - rr-score-volume
      - funnel-classification
      - execution-plan
      - next-day-plan
      - missing-data
      - conflict
  - 第三則 Telegram 資料依據 新增每層 source/status/use/limit/conflict 摘要，保留 v20.4.17 人話資料依據，不回退成 raw debug dump。
  - 新增 structural coverage verifier：
      - 計算 total visible decision/data layers
      - 計算 covered layers
      - 列出 missing slots
      - 列出 conflict slots
      - 檢查 fail-closed violation，阻擋 missing-source / unresolved-conflict 下的可買、通過、有效進場升格詞
      - coverage 必須 100% 才 pass
  - 新增 read-only artifact helper 與 CLI script，支援三組 fixture：
      - all_sources_available
      - missing_strategy_sample_source
      - ledger_position_conflict
  - 補 missing-source / unresolved-conflict fail-closed 測試，確認不可升格為可買 / 通過 / 有效進場。
  - QA blocker 修正：verifier 不只攔 `可買`，也攔 `通過`、`有效進場`；保守文案 `無有效進場` 不誤擋。

  ## 修改檔案

  - core/generator.py
      - VERSION 升至 v20.4.18
      - evidence manifest slot 結構補齊
      - third message evidence layer block 補齊
      - 新增 verify_structural_evidence_coverage
      - 新增 build_structural_evidence_artifact
      - 新增 structural fixture helper
  - scripts/generate_structural_evidence_artifact.py
      - 新增 read-only artifact CLI
      - 不連 live Telegram
      - 不寫 DB
      - 不改 schema
      - 不輸出 credential values
  - tests/test_generator_report.py
      - 更新版本斷言至 v20.4.18
      - 增加 manifest required key 檢查
      - 增加三組 structural artifact coverage/fail-closed 測試
  - tests/test_market_theme_evidence.py
      - 更新版本斷言至 v20.4.18

  ## 最小改動策略

  - 只在既有 Telegram generator / report_context / evidence_manifest / artifact 測試範圍內補 structural coverage。
  - 未重寫策略核心。
  - 未改買賣門檻。
  - 未改 DB schema / migration。
  - 未改 live Telegram delivery path。
  - 未改 production write path。
  - 未做 backfill。
  - 未清理或重構旁支模組。

  ## 契約影響

  - 使用者可見版本: v20.4.17 -> v20.4.18。
  - Telegram message list 順序維持：
      - messages[0]: 持倉
      - messages[1]: 未持倉 / 非持倉
      - messages[2]: short / evidence
      - include_detail=True 時 Details Backup 仍追加最後
  - 第三則 Telegram 新增標準 evidence layer 摘要，包含 source/status/use/limit/conflict。
  - report_context["evidence_manifest"] 每個可見決策 / 資料層 slot 新增 structural keys。
  - 新增 public helper:
      - verify_structural_evidence_coverage(messages, evidence_manifest)
      - build_structural_evidence_artifact(case="all_sources_available", now=None)
  - Verifier payload 保留 `coverage_pct`，並新增等價 alias `coverage_percent`。
  - 新增 artifact CLI:
      - scripts/generate_structural_evidence_artifact.py --case <case>
  - Artifact safety contract:
      - schema_change=false
      - data_write=false
      - live_telegram=false
      - credential_values_included=false
  - DB contract:
      - 無 schema change
      - 無 DB write
      - 無 production DML
      - 無 live Telegram

  ## 直接消費者同步

  - Owner 手機 Telegram 閱讀者:
      - 第三則可直接看到每層資料依據狀態、用途、限制與衝突。
  - QA verifier:
      - 可用 scripts/generate_structural_evidence_artifact.py 重跑三則 messages + evidence manifest + verifier。
      - blocking source status 存在時，可反證 `可買 / 通過 / 有效進場` 會讓 verifier fail。
  - 內部 report_context consumer:
      - evidence_manifest slot 保留既有欄位，新增 structural keys。
  - 內部 evidence_manifest consumer:
      - 可依 layer/target/source/status/use/limit/conflict/visible_refs 追溯可見層。
  - runner / CI coverage tests:
      - 新增 targeted tests 覆蓋三組 artifact case。

  ## 未影響模組

  - DB schema / migration / RLS / grant / policy / role / index / constraint 未改。
  - production write path 未改。
  - live Telegram send path 未改。
  - strategy decision core 未重寫。
  - market/theme 仍只作背景，不等於買點。
  - strategy sample 不可用時仍不納入買賣判斷。
  - 第一則 / 第二則持倉與未持倉卡片主結構未做無關改動。

  ## 已跑自檢命令

  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_write_pycache arch -arm64 .venv/bin/python -m py_compile core/generator.py scripts/generate_structural_evidence_artifact.py
      - result: passed
  - git diff --check
      - result: passed
  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_write_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py tests/test_market_theme_evidence.py
      - result: 119 passed, 169 warnings
      - warnings: third-party deprecation warnings from pyiceberg / pydantic / supabase
  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_write_pycache arch -arm64 .venv/bin/python scripts/generate_structural_evidence_artifact.py --case all_sources_available >/private/tmp/
    structural_all_sources_available.json
      - result: passed
      - verifier: messages=3 coverage=100.0 pass=True missing=[] fail_closed=[] conflicts=0
  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_write_pycache arch -arm64 .venv/bin/python scripts/generate_structural_evidence_artifact.py --case missing_strategy_sample_source >/private/tmp/
    structural_missing_strategy_sample_source.json
      - result: passed
      - verifier: messages=3 coverage=100.0 pass=True missing=[] fail_closed=[] conflicts=0
  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_write_pycache arch -arm64 .venv/bin/python scripts/generate_structural_evidence_artifact.py --case ledger_position_conflict >/private/tmp/
    structural_ledger_position_conflict.json
      - result: passed
      - verifier: messages=3 coverage=100.0 pass=True missing=[] fail_closed=[] conflicts=2
  - QA blocker targeted self-check:
      - injected `建準｜通過｜來源不足仍升格` => verifier pass=False, fail_closed_violations non-empty
      - injected `建準｜有效進場｜來源不足仍升格` => verifier pass=False, fail_closed_violations non-empty

  ## 殘留風險

  - 本輪只驗 structural coverage 100%，不驗資料合理度、不修 production ledger conflict。
  - Verifier 只針對 structural slot / fail-closed wording 做檢查，不等同 QA 完整驗收；目前已覆蓋 TASK 明列的可買 / 通過 / 有效進場。
  - Artifact fixture 是 read-only synthetic fixture，不代表 production data 已完整或無衝突。
  - 第三則顯示標準 status token 是本輪契約要求；v20.4.17 禁 raw engineering dump 的契約仍以不輸出 raw table/field/timestamp 為準。

  ## 旁支待辦

  - 若 Owner 要驗 production 真實資料合理度，需另開 production read-only evidence audit。
  - 若 Owner 要修 ledger / position_events 衝突，需另開 source-of-truth / ledger 稽核任務。
  - 若 QA 要擴大到 live runner 報文，需由 Architect 另行安排，不在 Tech 本輪自檢內。
