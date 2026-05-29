# QA_REPORT:

  ## 測試範圍

  本輪判定為 normal_patch / L2。未擴大到 full pytest、replay、backfill、live Supabase、live Telegram。

  已驗證：

  - TASK.md / CHANGELOG.md / worktree diff 對齊。
  - read-only loader contract。
  - provider 直接消費者。
  - Telegram header 與手機 summary。
  - support_level=strong 只能作為負面測試，不能被接受。
  - clean/fresh runner 反證：無 DB source 時不得 fake confirmed。

  執行命令：

  - PYTHONPATH=.qa_tmp:. arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence.py tests/test_generator_report.py tests/test_notifier.py
      - 結果：93 passed, 161 warnings
  - git diff --check
      - 結果：passed
  - 額外 QA 反證：patch _build_client=None 後呼叫 generator.market_theme_summary_evidence(..., None)
      - 結果：missing-source False production_db
      - 手機摘要首句：證據：production 來源不足，不作確認。

  ## 風險預算與停止條件

  本輪最值得抓的風險：

  1. DB source 缺失或錯誤時被 runtime / watchlist 補成 confirmed。
      - 驗證：loader fail-closed tests + QA 額外 fresh-run 反證。
      - 停止條件：missing-source/source-error/absent/insufficient-data 都不得 confirmed=true。
  2. support_level=strong 被回收成合法 enum。
      - 驗證：掃描本輪變更與負面測試。
      - 停止條件：accepted enum 僅 confirmed/supporting/weak/invalidated，strong 只出現在 fail-closed 測試或說明。
  3. 手機 Telegram 讓 Owner 把 evidence confirmed 誤讀成可買。
      - 驗證：summary 閱讀順序與既有 fixture。
      - 停止條件：先出現今日結論 / 新倉結論，再出現 evidence；confirmed evidence 必須帶 不代表可買 限制。

  ## 關聯風險掃描

  可吸收 diff：

  - core/generator.py
  - core/market_theme_evidence.py
  - tests/test_generator_report.py
  - tests/test_market_theme_evidence.py
  - CHANGELOG.md
  - services/market_theme_evidence_store.py

  注意：services/market_theme_evidence_store.py 目前是 untracked，不在 git diff --name-status 內，但 core/generator.py 已 import 它。Architect 合併時必須把此 untracked 新檔一併吸收；若只套 tracked diff，會造成 import
  failure。

  worktree 殘留 / 不建議吸收：

  - .qa_tmp/config.py 是本地測試 shim，不在 git status，不能當產品 diff。
  - CURRENT_STATE.md 仍舊版屬 Architect 收口文件，不是本輪 Tech diff。

  清理 / 瘦身 / refactor 任務證據表：不適用，本輪不是清理任務。

  ## 跨區塊語意一致性

  版本契約一致：

  - core/generator.py VERSION 已是 v20.4.3。
  - Telegram snapshot 測試已同步 v20.4.3。

  Source contract 一致：

  - loader accepted support levels 不含 strong。
  - confirmed 條件限定 support_level in confirmed/supporting、evidence_status=confirmed、freshness=fresh。
  - provider 保留 fail-closed status，不把 DB 缺失壓成 confirmed。

  手機閱讀順序：

  - 既有 fixture 驗證 🧭 新倉：無有效進場。 早於 evidence summary。
  - confirmed wording 後仍有 限制：題材可追蹤，不代表可買。
  - fail-closed wording 是短句：證據：production 來源不足，不作確認。

  ## 使用者誤讀風險

  目前未看到會讓 Owner 誤判買入的輸出。confirmed evidence 只說市場/題材支持成立，並保留不可買限制；缺資料也沒有被寫成市場偏弱或 confirmed。

  殘留風險：若 production role / RLS 不可讀，正式 runner 會 fail closed 為來源不足，這符合本輪契約，但 Owner 可能需要後續驗 production read-only 權限，不屬本輪 live 驗證範圍。

  ## 質疑與反證

  主動質疑 1：無本地 cache / 無 DB source 時，generator 是否仍會用 results_map 或 runtime 診斷 fake confirmed？

  - 反證：QA 額外直接呼叫 market_theme_summary_evidence，patch DB client missing。
  - 結果：missing-source、confirmed=False、手機摘要不作確認。

  主動質疑 2：strong 是否被 accepted enum 或 mapping 接回 confirmed？

  - 反證：掃描本輪 loader / provider / tests / changelog。
  - 結果：loader accepted enum 不含 strong；唯一 support_level="strong" 是負面測試，預期 source-error。

  主動質疑 3：Tech 宣稱新增 loader，但 git diff 是否完整包含？

  - 反證：git diff --name-status 不含新 service，git ls-files --others --exclude-standard 顯示 services/market_theme_evidence_store.py。
  - 結果：行為可接受，但合併條件必須明確納入 untracked 新檔。

  ## 未測項目

  - 未連 production DB。
  - 未驗 production read-only role / RLS / 實際資料內容。
  - 未做 live Supabase write、backfill、replay、live Telegram。
  - 未跑 full pytest，符合 normal_patch / L2 停止條件。

  ## QA 結論

  conditional pass

  條件：Architect 吸收 diff 時必須包含 untracked 的 services/market_theme_evidence_store.py，不能只套 git diff --name-status 顯示的 tracked files。若該檔未被納入，本輪應視為阻塞，因 core/generator.py 會 import 不存在的
  module。
