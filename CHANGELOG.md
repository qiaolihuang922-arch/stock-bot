# CHANGELOG:

  ## 任務尺寸與風險

  - 任務類型：normal_patch。
  - 風險判斷：使用者可見 Telegram 報文與版本變更，未改策略 decision、DB schema/write、live Telegram、maturity artifact schema。

  ## 修改內容

  - 將報文版本升至 v20.4.20。
  - 第三則 Telegram evidence 報文改為中文人話分層摘要，不再輸出 source:/status:/use:/limit:/conflict: raw slot dump。
  - 保留內部 evidence_manifest / maturity artifact / verifier 的 machine-readable 欄位與 fail-closed 能力。
  - 摘要 `🔥 最強` 改成只允許有效進場標的；若新倉無有效進場或候選只是追蹤/不可行動，一律顯示 `無有效進場標的`，不顯示排序/評級。
  - 持倉非加碼卡片改顯示 新倉 RR：不適用（既有持倉），不顯示新倉 RR 數字。
  - strategy sample 不可用時，持倉/未持倉卡片顯示 策略樣本：不可用，本次不納入判斷，不顯示樣本數、勝率、回測 RR / 報酬等數字。
  - handoff gate 同步 v20.4.20，並新增第三則不得暴露 raw evidence slot 欄位的檢查。

  ## 修改檔案

  - core/generator.py
  - tests/test_generator_report.py
  - tests/test_market_theme_evidence.py
  - tools/cao_agent/check_evidence_handoff_gate.sh

  ## 最小改動策略

  - 只改 presentation layer、版本常量、對應測試與直接 gate consumer。
  - 不改 BUY/SELL/加減碼/停利停損策略。
  - 不改 DB schema、production write path、read-only artifact schema、maturity verifier required keys。

  ## 契約影響

  - Telegram message list 順序不變：messages[0] 持倉、messages[1] 未持倉、messages[2] short/evidence；include_detail=True 時 Details Backup 仍追加最後。
  - 使用者可見第三則 evidence contract 改為人話摘要；內部 manifest/artifact 仍保留 source/status/use/limit/conflict。
  - `🔥 最強` contract 改為有效進場限定；不可買、可準備、僅追蹤、source 不合格標的不得出現在最強推薦行。
  - 持倉非加碼 RR 顯示 contract 改為新倉 RR 不適用。
  - strategy sample unavailable card display contract 改為不可用/不納入判斷，不顯示回測數字。
  - maturity report 仍回傳 maturity_score=100，安全旗標維持 false。

  ## 直接消費者同步

  - Telegram message consumer：第三則仍是同一位置，但內容改為人話 evidence 摘要。
  - Owner 手機閱讀者：第三則不再看到 raw slot/status dump。
  - evidence_manifest / maturity artifact / verifier：內部欄位保留，測試確認未移除 machine-readable keys。
  - QA fixture：新增/更新第三則 raw slot hidden、無有效進場不顯示推薦感最強、持倉非加碼 RR、strategy sample unavailable card 測試。
  - Architect gate：check_evidence_handoff_gate.sh 同步 v20.4.20 與第三則 raw slot 禁止檢查。

  ## 未影響模組

  - production DB schema / migration / RLS / grant / policy / role / index / constraint。
  - production DB write、backfill、live Telegram delivery。
  - strategy decision core、BUY/SELL/加減碼/停損停利門檻。
  - read-only artifact safety flags 與 maturity required keys。

  ## 已跑自檢命令

  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m py_compile core/generator.py scripts/generate_structural_evidence_artifact.py：passed。
  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py：88 passed，177 warnings。
  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_market_theme_evidence.py：36 passed，13 warnings。
  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py tests/test_market_theme_evidence.py：124 passed，177 warnings。
  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python scripts/generate_structural_evidence_artifact.py --maturity-report --case production_all_sources_available：passed，
    maturity_score=100，generator_version=v20.4.20。
  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python scripts/generate_structural_evidence_artifact.py --maturity-report --case production_all_sources_available > /private/tmp/
    evidence_maturity_report_v20_4_20.json && tools/cao_agent/check_evidence_handoff_gate.sh . /private/tmp/evidence_maturity_report_v20_4_20.json：passed。
  - git diff --check：passed。

  ## 殘留風險

  - 未做 full pytest；本輪只跑與 Telegram report / market theme / maturity handoff 直接相關的測試。
  - strategy sample 不可用時卡片一律隱藏回測數字，若未來有獨立於 strategy sample 的合法回測來源，需要另開 contract 區分。

  ## 旁支待辦

  - Telegram reply markup 附著最後一則 message 的 delivery consumer 風險仍未處理。
  - production ledger 與 Owner 認知差異未在本輪修復；本輪只做保守顯示與人話摘要。
