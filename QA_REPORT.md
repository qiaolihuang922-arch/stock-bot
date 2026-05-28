# QA_REPORT:

  ## 測試範圍

  本輪為最終一致性複核，不擴大成 full pytest / replay / backfill。已讀取 TASK.md、CHANGELOG.md、git status、git diff --stat、相關 diff 與局部源碼。

  已驗證 worktree 變更檔案只有：

  - CHANGELOG.md
  - core/market_theme_evidence.py
  - core/generator.py
  - tests/test_market_theme_evidence.py
  - tests/test_generator_report.py
  - tests/test_notifier.py

  可吸收 diff：上述 5 個候選實作/測試檔與重寫後 CHANGELOG.md。
  worktree 殘留：未見額外 tracked/untracked 殘留；不建議整包合併超出上述清單。

  執行命令：

  - arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence.py tests/test_generator_report.py tests/test_notifier.py
  - 結果：69 passed, 21 warnings
  - 額外 QA smoke：直接驗證 freshness=stale/unavailable/missing 即使 freshness_reason=same_trade_date 仍降級 stale，並驗證 notifier.send_many() 最後 summary 原文與 reply_markup=None contract。
  - 結果：extra smoke passed

  ## 風險預算與停止條件

  本輪最值得抓的 3 個風險：

  1. CHANGELOG.md 與實際 diff 不一致。
     驗證：比對 git diff --stat、git diff --name-only 與 CHANGELOG 修改檔案/契約描述。
     停止條件：CHANGELOG 覆蓋五個指定檔案、版本、契約、未影響模組與殘留風險。
  2. stale freshness precedence 被 header/文案測試掩蓋。
     驗證：既有測試加額外 smoke，確認 freshness 本身為 stale/unavailable/missing 時優先降級。
     停止條件：不得 confirmed，summary 顯示 stale 限制，不產生可買暗示。
  3. Telegram message list / notifier payload shape 被 evidence summary 改壞。
     驗證：tests/test_notifier.py 與額外 smoke 確認最後 message 原文保留、非最後訊息無 reply markup、最後訊息預設 reply_markup=None。
     停止條件：payload shape 不變且 header 為 v20.2.0。

  ## 關聯風險掃描

  CHANGELOG.md 已覆蓋 Architect 指定的 5 個候選檔案：core/market_theme_evidence.py、core/generator.py、tests/test_market_theme_evidence.py、tests/test_generator_report.py、tests/test_notifier.py。

  版本/header：core/generator.py 為 VERSION = "v20.2.0"；測試期望已同步 v20.2.0；局部 pytest 通過。

  DB/schema/cache/external provider/live write/backfill/live Telegram：本輪 diff 未新增 schema、migration、DB payload、cache、external provider、live Telegram delivery 或 backfill 寫入。core/generator.py 中既有 Supabase/
  backfill 字樣屬舊路徑，非本輪新增 diff。

  清理 / 瘦身 / refactor 證據表：本輪不是清理任務，不適用 path / claim / evidence / risk / action 表阻塞條件。

  ## 跨區塊語意一致性

  Owner 手機閱讀順序檢查：summary header 先顯示 v20.2.0，再顯示市場、今日結論、原因、新倉不可買，之後才是市場 / 題材 evidence。confirmed 場景仍保留「新倉：無有效進場」在 evidence 前方，避免 Owner 先看到 confirmed 誤判可
  買。

  confirmed / weak / mixed / stale / absent 五類 fixture 有測試覆蓋。freshness precedence block 通過：required source stale/unavailable/missing 不會因 freshness_reason=same_trade_date 變 confirmed。

  高風險文案：AI / 電子供應鏈仍偏多 主線句已不再由 market_execution_bridge_lines 輸出；測試也覆蓋不得出現。

  ## 使用者誤讀風險

  目前可接受。confirmed 文案有同屏限制「題材可追蹤，不代表可買」，且新倉仍顯示無有效進場。stale 場景顯示「市場資料過期，本輪不判斷主線」，不會包裝成市場主線仍在。

  殘留後續風險：formatter 只列前三個 runtime source freshness；若未來要做完整 source audit，需另開任務，不阻塞本輪。

  ## 質疑與反證

  主動反證 1：CHANGELOG 是否只說改文件、但漏掉產品 diff。結果：CHANGELOG 已明確描述 core/market_theme_evidence.py 與 core/generator.py 的既有候選功能 diff，並列出三個測試檔同步。

  主動反證 2：同交易日 reason 是否可能覆蓋 stale freshness。結果：既有測試與額外 smoke 均證明 freshness 本身優先，不能 confirmed。

  主動反證 3：notifier 是否把最後 summary header 或 payload shape 改壞。結果：send_many() 仍逐則送出，最後 summary 原文保留，預設 reply_markup=None，測試與額外 smoke 通過。

  ## 未測項目

  未跑 full pytest、正式 replay/backfill、正式 Supabase write、live Telegram delivery；符合 Architect 指令與本輪最終一致性複核範圍。未做外部 provider 真實資料驗證，因 TASK 明確禁止本輪接外部 provider / live path。

  ## QA 結論

  通過

  CHANGELOG 與目前 worktree diff 已一致；freshness precedence、v20.2.0 header、no DB/schema/cache/live/backfill、message list/notifier payload shape 均通過本輪驗證。
