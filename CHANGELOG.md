# CHANGELOG:

  ## 任務尺寸與風險判斷

  - 任務尺寸：risk_patch（沿用 TASK.md 對 production source-of-truth / fail-closed integrity check 的分級）。
  - 本次實作範圍：只修主 repo 吸收候選後的單一 blocker，屬於 risk_patch 內的最小 blocker patch；未擴大到策略、報文文案、DB schema、live delivery 或完整 integrity 矩陣重作。

  ## 修改內容

  - 修正 --full-integrity-check-json 在 _build_readonly_client() 明確回傳 None 時仍可能透過內層 config / fallback 讓 source integrity 變成 passed 的問題。
  - CLI read client 缺失時，full integrity JSON 現在會注入 missing-source source check，讓：
      - production_db_readonly = blocked
      - may_data_available = blocked
      - market_theme_source_of_truth = blocked
  - 保留 dry-run report generator stdout capture：stdout 第一層仍只輸出 JSON，generator warning 只進 diagnostics / blocked_reasons。
  - 補強 regression test，鎖住三個 source integrity 欄位不得 fallback 成 passed。

  ## 修改檔案

  - core/generator.py
      - build_may_data_strategy_report_full_integrity_check() 新增可選 source_check 參數，用於 CLI 已知 missing-source 時避免內層重新建 production client。
  - scripts/smoke_market_theme_evidence_readonly.py
      - _build_readonly_client() 回傳 None 且執行 --full-integrity-check-json 時，傳入 _missing_source_consumption_report() 作為 fail-closed source check。
  - tests/test_market_theme_evidence.py
      - 補上 missing read client + noisy report generator 情境下 may_data_available 與 market_theme_source_of_truth 也必須 blocked 的斷言。

  ## 最小改動策略

  - 只處理 Architect 指定的 blocker path。
  - 不重構 formatter / runner / DB layer。
  - 不改策略門檻、持倉狀態機、Telegram 使用者可見報文或版本 header。
  - 不修旁支 warning，不擴大測試矩陣。

  ## 契約影響

  - JSON 欄位形狀未改。
  - --full-integrity-check-json 契約收緊：當 CLI read client 明確 missing/source-error 時，source integrity 不得因本機 config 或 fallback 轉 passed。
  - build_may_data_strategy_report_full_integrity_check() 增加 optional source_check 注入參數；既有呼叫方不傳時行為維持原本路徑。
  - 不改 Telegram message list、payload shape、報文分組、使用者可見文案或 header version。

  ## 直接消費者同步

  - 已同步直接 CLI consumer：scripts/smoke_market_theme_evidence_readonly.py --full-integrity-check-json。
  - 已同步直接測試 consumer：tests/test_market_theme_evidence.py。
  - 其他既有 direct caller 可不變更，因 source_check 是 optional additive parameter。

  ## 未影響模組

  - 未 live Telegram。
  - 未 DB write。
  - 未 schema / RLS / grant / policy / role change。
  - 未 backfill / replay。
  - 未改 watchlist。
  - 未改策略買賣門檻、RR、停損停利、持倉狀態機。
  - 未改 Telegram 使用者可見報文與 v20.4.6 header。

  ## 已跑自檢命令

  - arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence.py::MarketThemeEvidenceTest::test_readonly_smoke_cli_full_integrity_json_captures_report_stdout_warning -q
      - 結果：1 passed。
  - arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence.py tests/test_generator_report.py tests/test_notifier.py -q
      - 結果：105 passed。

  ## 殘留風險

  - 自檢使用 mocked read client / report generator 驗證 fail-closed path；未執行 live production DB read。
  - 測試輸出仍有既有 dependency deprecation warnings，與本 blocker 無關。
  - 本輪不宣告 QA 通過，僅代表 Tech 交付前自檢通過。

  ## 旁支待辦

  - worktree 內 CHANGELOG.md 在本輪開始前已是 modified；本輪依 Architect 指令未直接編輯，最終 CHANGELOG 由本回答提供給 runner 寫入。
  - dependency deprecation warnings 可另開環境維護任務處理；不屬於本 blocker。
