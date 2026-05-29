# QA_REPORT:

  ## 測試範圍

  本輪 QA 風險預算判定為 normal_patch / L2，不擴大到 full pytest、replay、backfill、live DB 或 live Telegram。

  可吸收 diff 僅限：

  - CHANGELOG.md
  - core/generator.py
  - core/market_theme_evidence.py
  - tests/test_generator_report.py
  - tests/test_market_theme_evidence.py

  git status --short 與 git diff --name-only 顯示只有上述 5 檔變更；未發現 worktree 其他殘留需要合併。

  已執行 Architect 指定命令：

  TMPDIR=.qa_tmp PYTHONPATH=.qa_tmp:. arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence.py tests/test_generator_report.py tests/test_notifier.py tests/test_strategy_evidence.py

  結果：100 passed, 13 warnings in 0.60s。warnings 為既有相依套件 deprecation。

  另跑 git diff --check：通過，無 whitespace error。

  ## 風險預算與停止條件

  本輪最值得抓的 3 個風險：

  1. runtime_diagnostic/runtime/local/cache/worktree/test_fixture 欄位完整時被誤升為 confirmed/ready。
      - 驗證：補臨時 Python fixture，逐一構造 6 種非持久 source_family。
      - 結果：全部 confirmed=False，source_status != ready，confidence != confirmed。
      - 停止條件：確認非持久 source 不可越界成 confirmed。
  2. production source 足夠時，頂層 source_family 被 report_derived 題材文字污染。
      - 驗證：構造 production_db watchlist_breadth + production_db market_index + report_derived theme text。
      - 結果：confirmed=True、source_status=ready、source_family=production_db、confidence=confirmed。
      - 停止條件：report-derived 只留 detail trace，不污染 top-level boundary。
  3. Telegram 手機閱讀順序與 v20.4.2 header。
      - 驗證：tests/test_generator_report.py 與 tests/test_market_theme_evidence.py 內含 summary index order、header、wording 斷言。
      - 結果：v20.4.2 已同步；新倉：無有效進場 早於 evidence wording；缺來源時只顯示短句 證據：production 來源不足，不作確認。。

  ## 關聯風險掃描

  git diff --stat 顯示只改 5 檔，範圍符合 Architect 指令。

  關鍵字掃描 diff：未見 schema/migration/SQL 檔案變更；未見 backfill/replay write path、watchlist、live Telegram、live Supabase 實作變更。出現的 BUY/SELL/RR/threshold/write/backfill/watchlist 多為 CHANGELOG 非目標描述、
  既有測試文案或 forbidden_effects 文字，非策略門檻或寫入路徑修改。

  services/strategy_evidence.py 未改；以 tests/test_strategy_evidence.py 作為直接消費者回歸，通過。

  ## 跨區塊語意一致性

  TASK 要求 v20.4.2；core/generator.py 已為 VERSION = "v20.4.2"，相關 generator/report 測試期望已同步。

  CHANGELOG.md 與 diff 一致：本輪主軸是 source-family gate、v20.4.2 header 與短 evidence wording；未宣稱已接 production DB live data，也明確保留「未連 production DB」殘留風險。

  market/theme evidence 契約一致：

  - 非持久來源不 confirmed/ready。
  - confirmed/ready 時 top-level source_family 收斂為 production_db 或 owner_approved_persistent。
  - sources/source_family_details/limitations 仍可保存 runtime/report-derived trace。

  ## 使用者誤讀風險

  按 Owner 手機閱讀順序檢查：summary 先出行動結論，例如 新倉：無有效進場，再出 evidence 短句；缺來源不再用 absent/missing-source 長清單讓 Owner 誤讀成外部市場真的不強。

  缺 production source 時 wording 是：

  - 證據：production 來源不足，不作確認。
  - 詳情：runtime 觀察僅供診斷，非確認來源。

  這能明確區分「不可確認」與「市場不存在」，且不會把 runtime 診斷包裝成買入支持。

  ## 質疑與反證

  新增反證不是只重跑 Tech 自檢：

  - 直接構造 runtime_diagnostic/runtime/local/cache/worktree/test_fixture 六種完整欄位 source，確認都不能 confirmed/ready。
  - 直接構造 production sufficient + report-derived theme text 混合 source，確認 top-level source_family 仍是 production_db。
  - 掃描 diff 範圍與 forbidden 關鍵字，確認本輪沒有把 wording/source boundary patch 擴成 schema、write、watchlist、backfill 或策略門檻變更。

  未發現 TASK / CHANGELOG / diff 不一致。

  ## 未測項目

  - 未連 production DB，未驗實際 table/view 的資料品質與 freshness。
  - 未做 replay/backfill dry-run。
  - 未做 live Supabase write 或 live Telegram delivery，且本輪禁止執行。
  - 未跑 full pytest；依 TASK normal_patch / L2 與 Architect 指定範圍，本輪停止於 evidence/generator/notifier/strategy evidence 直接消費者測試。

  ## QA 結論

  通過
