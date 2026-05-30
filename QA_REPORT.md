# QA_REPORT:

  ## 測試範圍

  本輪 QA 風險預算按 Architect 指令收斂為第二次返工 blocker 驗證，不擴成 full pytest / replay / backfill。

  - 驗證文件：TASK.md、CHANGELOG.md、git diff、core/generator.py、scripts/smoke_market_theme_evidence_readonly.py、tests/test_market_theme_evidence.py
  - 指定測試：tests/test_market_theme_evidence.py
  - 額外反證：主 repo 等價情境 _build_readonly_client=None + noisy generate_report(dry_run=True)，確認 stdout 第一層仍是 JSON，且 source integrity 不 fallback passed
  - 靜態掃描：確認本 diff 無 migration/schema 檔、無 live Telegram delivery、dry-run 路徑不執行 DB write block

  ## 風險預算與停止條件

  最值得抓的風險：

  1. missing-source/source-error 被內層 fallback 重建 client 後誤判 production_db_readonly=passed
      - 驗證：測試與額外反證均要求 production_db_readonly、may_data_available、market_theme_source_of_truth 為 blocked
      - 停止條件：三欄任一變 passed 即阻塞
  2. generator stdout warning 污染 CLI JSON stdout，導致 Architect/runner json.loads 失敗
      - 驗證：額外反證直接 json.loads(stdout)
      - 停止條件：stdout 第一層不是 JSON 或 warning 出現在 JSON 外即阻塞
  3. 本輪 dry-run 意外做 DB write / live Telegram / schema change
      - 驗證：diff file list、dry_run=True write block 檢查、JSON flags
      - 停止條件：出現 migration/schema diff、live send path、dry-run 仍呼叫 write functions 即阻塞

  ## 關聯風險掃描

  - scripts/smoke_market_theme_evidence_readonly.py:171-184：_build_readonly_client() 回傳 None 時，--full-integrity-check-json 會注入 _missing_source_consumption_report()，避免進入內層 production client fallback。
  - core/generator.py:4618-4626：新增 source_check 注入後，已知 missing/source-error 可直接作為 source-of-truth，不再被 client 或 config 二次覆蓋。
  - core/generator.py:4655-4662：source 未 passed 時三個 source integrity 欄位 fail closed：production_db_readonly=blocked、may_data_available=blocked、market_theme_source_of_truth=blocked。
  - core/generator.py:4631-4644：dry-run generator stdout 被 capture 到 diagnostics / blocked_reasons，不污染 CLI JSON stdout。
  - core/generator.py:5797-5845：dry_run=True 時跳過 record_daily_signals、record_daily_snapshots、record_strategy_evidence。
  - 本 worktree diff 仍包含完整 integrity check 候選實作與 CHANGELOG.md 修改；本輪可吸收的重驗結論只覆蓋 Architect 指定的 blocker patch，不等於建議整包無條件合併。

  ## 跨區塊語意一致性

  - Integrity JSON 契約一致：missing client 與 source-error 反證中，source integrity 三欄同時 blocked，沒有出現「DB 不可讀但 market_theme_source_of_truth 顯示 production confirmed」的語意衝突。
  - Fresh runner dry-run 一致：report sample 可生成時 fresh_runner_dry_run.report_generated=passed，但 source 缺失仍保留 blocked，不會把「報文可產生」誤解成「production evidence 可用」。
  - 使用者可見版本：core/generator.py 仍為 VERSION = "v20.4.6"，本輪未改 Telegram header 或 message list contract。

  ## 使用者誤讀風險

  Owner / Architect 第一眼看到的是 CLI JSON，不是 live Telegram。已驗證 stdout 可直接 json.loads，generator warning 不會跑到 JSON 外造成 runner 誤讀或 parser 失敗。

  手機報文部分本輪未改正式 Telegram 文案；測試 fixture 仍按 summary / cards / funnel 的閱讀順序檢查基本矛盾，且 missing-source 不會被包裝成可買或 production passed。未執行 live Telegram。

  ## 質疑與反證

  已跑命令：

  - TMPDIR=.qa_tmp PYTHONPATH=.qa_tmp:. arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence.py -q
      - 結果：33 passed, 13 warnings

  額外反證：

  - patch _build_readonly_client=None
  - patch generate_report(dry_run=True) 先印 warning 再回傳 report messages
  - 執行 smoke.main(["--trade-date", "2026-05-29", "--full-integrity-check-json"])
  - 驗證結果：
      - exit code = 2
      - stdout 可 json.loads
      - production_db_readonly=blocked
      - may_data_available=blocked
      - market_theme_source_of_truth=blocked
      - warning 只在 diagnostics / blocked_reasons
  - 另以 source_check.table_status.market_theme_confirmed_evidence="source-error" 且傳入非 None client 反證：三個 source integrity 欄位仍 blocked，沒有 fallback 成 production passed。

  git diff --check 通過。

  ## 未測項目

  - 未連 production DB read-only credentials；本輪依 Architect 指令驗證 mocked / 等價 fail-closed path。
  - 未跑 full pytest、replay、backfill、live Telegram。
  - 未驗證整份真實長 Telegram 報文；本輪未改使用者可見報文 contract，只驗證 fixture 層的跨區塊矛盾與 JSON 誤讀風險。

  ## QA 結論

  通過

  本輪第二次返工 blocker 已修正：_build_readonly_client=None 與 source-error 不會再讓 full integrity JSON 的 production source integrity fallback passed；stdout 仍是純 JSON；未發現 DB write、live Telegram 或 schema
  change。
