# QA_REPORT: market/theme 五月歷史回寫 conditional pass 重驗

  ## 測試範圍

  本輪只重驗 Architect 指定的上一輪 conditional pass 條件，未擴大到 live DB/write/full replay。

  - 讀取 TASK.md、CHANGELOG.md、git status --short、git diff --stat、指定三檔 diff。
  - 驗證 CHANGELOG.md 已列出 CHANGELOG.md 為交付文件 diff。
  - 驗證已移除「未直接編輯 CHANGELOG.md」或等價矛盾句。
  - 驗證 CHANGELOG.md 仍準確描述 scripts/backfill_market_theme_sources.py 與 tests/test_market_theme_source_backfill.py。
  - 快速確認 forbidden daily_signal_snapshot 反證測試仍存在並可執行。
  - 執行：.venv/bin/python -m pytest tests/test_market_theme_source_backfill.py -q，結果 11 passed in 0.12s。

  ## 風險預算與停止條件

  本輪最值得抓的風險：

  1. 交付摘要仍和 worktree diff 矛盾。
      - 驗證：比對 git diff --name-only 與 CHANGELOG.md 修改檔案段落。
      - 停止條件：三個 diff 檔案一致列出即可停止，不追查全 repo。
  2. 舊 conditional pass 的矛盾句殘留，導致 Architect 吸收錯誤交付事實。
      - 驗證：rg 搜尋「未直接編輯 CHANGELOG」、舊 production audit 檔名與舊摘要關鍵字。
      - 停止條件：搜尋無命中即可停止。
  3. forbidden daily_signal_snapshot guard 被移除或只剩表面欄位。
      - 驗證：檢查測試是否同時覆蓋 report blocked 與 write client 無呼叫，並重跑局部測試。
      - 停止條件：指定測試存在且局部測試通過即可停止。

  ## 關聯風險掃描

  git diff --name-only 只有：

  - CHANGELOG.md
  - scripts/backfill_market_theme_sources.py
  - tests/test_market_theme_source_backfill.py

  可吸收 diff 僅限上述三檔；不建議 Architect 將整個 worktree 或未檢查旁支一併視為可合併。

  CHANGELOG.md 已在修改內容與修改檔案中列出 CHANGELOG.md，並描述它是交付文件 diff。rg 搜尋舊矛盾句與舊檔名無命中，未看到上一輪「未直接編輯 CHANGELOG.md」或舊 production audit 三檔摘要殘留。

  ## 跨區塊語意一致性

  TASK.md 是 risk_patch / L3，但 Architect 本輪明確要求只重驗 conditional pass 條件；本次 QA 未擴大到 live DB/write/full replay，符合本輪收斂指令。

  CHANGELOG.md 對產品/測試 diff 的描述與實際 diff 一致：

  - script：report shape、May range guard、forbidden source family/lineage、latest membership blocked、只 upsert confirmed evidence、read-after-write metrics。
  - test：dry-run report shape、May range guard、forbidden daily_signal_snapshot、missing required fields、execute path、read-after-write trend metrics。
  - 未影響模組：未改 Telegram/header/VERSION、未 live write、未正式 backfill，與 TASK 非目標一致。

  ## 使用者誤讀風險

  本輪不是 Telegram / summary / dashboard 顯示任務，TASK.md 也明確寫手機閱讀路徑不適用。已快速確認 CHANGELOG.md 沒有宣稱 Telegram 內容或 header 改動；因此 Owner 不會因本輪交付摘要誤讀成「已正式回寫」或「已可 live 發
  報」。

  仍需注意：CHANGELOG.md 的自檢段落提到候選 diff 統計為「2 個產品/測試檔案」，但目前 worktree 還有 CHANGELOG.md 交付文件 diff。這在上下文中可接受，因同段修改檔案已明列三檔；不構成本輪阻塞。

  ## 質疑與反證

  主動反證不是只重跑 Tech 自檢：

  - 檢查 forbidden daily_signal_snapshot 測試不只驗欄位存在。測試會把 source_family 與 lineage.source_tables 改成 daily_signal_snapshot，確認 report blocked、validated_rows=0、pollution_guard=blocked，並呼叫
    upsert_source_payloads 預期丟 ValueError，最後驗證 fake client calls=[]，代表不會寫入。
  - script 端仍有 FORBIDDEN_SOURCE_FAMILIES 與 FORBIDDEN_LINEAGE_SOURCE_TABLES 包含 daily_signal_snapshot，validation 會產生 forbidden source_family 與 forbidden lineage source_tables。
  - report 仍固定輸出 daily_price_signal_snapshot_rewrite = forbidden_as_primary_result 與 uses_only_daily_signal_snapshot = False。

  ## 未測項目

  - 未執行 live Supabase write。
  - 未執行正式 backfill。
  - 未跑 full pytest、full replay、production audit。
  - 未驗證真實 production DB read-after-write，因 Architect 本輪明確要求只重驗 conditional pass 條件。

  ## QA 結論

  通過。

  上一輪 conditional pass 條件已滿足：CHANGELOG.md 已列為交付文件 diff，舊矛盾句已移除，摘要與目前三檔 diff 一致，forbidden daily_signal_snapshot 反證測試仍存在且局部測試通過。
