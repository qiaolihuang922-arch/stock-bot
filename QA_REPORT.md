# QA_REPORT:

  ## 測試範圍

  本輪判定為 process / audit，不是產品修補；QA 未擴成 full pytest、replay、backfill 或 live smoke。

  已讀取與核對：

  - TASK.md
  - CHANGELOG.md
  - git status --short
  - git diff --stat
  - git diff --name-only
  - 指定鏈路的必要局部源碼：core/generator.py、core/market_theme_evidence.py、services/market_theme_evidence_store.py、services/position_store.py、services/cross_day_context.py、services/strategy_evidence.py、services/
    daily_snapshot_store.py、services/signal_store.py、.github/workflows/stock-bot.yml、main.py

  已執行驗證：

  - arch -arm64 .venv/bin/python -m pytest tests/test_position_store.py tests/test_cross_day_context.py tests/test_market_theme_evidence.py tests/test_strategy_evidence.py
  - 結果：41 passed, 17 warnings
  - 補充 inline 反證：runtime-only market/theme evidence 不會 confirmed；support_level=strong 回 source-error；空 production rows 回 absent。

  ## 風險預算與停止條件

  本輪最值得抓的風險：

  1. PASS 被 Owner 誤讀成端到端已完成。
     驗證：核對 market_theme_confirmed_evidence writer / ingestion / backfill / RLS / production smoke 是否仍缺。
     結果：Tech 已標出 read-only-chain-incomplete，QA 確認不能視為可恢復開發完成態。
  2. fake / runtime / report-derived fallback 被升格成 confirmed。
     驗證：讀 core/market_theme_evidence.py source family guard，並用 inline 反證 runtime-only path。
     結果：runtime-only 顯示「production 來源不足」，confirmed=False。
  3. process audit diff 被誤當產品 diff 合併。
     驗證：git diff --name-only 只有 CHANGELOG.md。
     結果：可吸收 diff 僅是本輪交付文件；沒有產品代碼、測試、SQL、runner diff。

  停止條件已達：已核對 Tech matrix 正向結論、補反證、確認無產品 diff、未執行 live write / Telegram / backfill。

  ## 關聯風險掃描

  可吸收 diff：

  - CHANGELOG.md 的 audit matrix 文件更新。

  worktree 殘留 / 不可當產品合併內容：

  - 未發現產品代碼 diff。
  - git status --short 顯示交付文件變更；Architect 收口時已把 `CHANGELOG.md` 的「零 diff / git status」描述改為「產品代碼零 diff，交付文件有 diff」。這是交付敘述修正，不是產品行為風險。

  主要鏈路反證結果：

  - positions missing-source / source-error：load_positions() 回 {} 並設 warning；generate_report() 讀 warning 後提前輸出 fail-closed summary，未 fallback 成全 watchlist 0 股。
  - position events missing-source / source-error：回 unavailable summary；只有 query 成功且空資料才是全 0 event summary。
  - market/theme evidence：loader 要求 support_level in confirmed/supporting、evidence_status=confirmed、freshness=fresh；strong 被 inline 反證為 source-error。
  - runtime/report-derived：runtime diagnostic 只顯示診斷，不 confirmed。
  - cross-day context：source-error / insufficient-data 時清空 previous state/action/weight，不把 same-run local context 升格為跨日記憶。
  - DB consumption：market_daily_bars 仍是 write-only；signal_runs/items/outcomes 目前偏 reference-only；strategy_outcome_metrics fresh runner writer 狀態仍 conditional。這些已被 Tech matrix 標為風險或旁支 next action。

  ## 跨區塊語意一致性

  本輪不改 Telegram / summary / dashboard 輸出；core/generator.py 版本仍是 v20.4.3，符合 TASK 的「audit 不升版」。

  以 Owner 手機閱讀順序檢查相關 fail-closed 文案：

  - 缺持倉來源時，開頭即顯示 warning、新倉：無有效進場、持倉 unavailable、production 來源不足。
  - market/theme runtime fallback 文案明確寫「runtime 觀察僅供診斷，非確認來源」。
  - 未看到把不可買、僅診斷或缺資料包裝成可買建議的新增 diff。

  ## 使用者誤讀風險

  最大誤讀風險不是 Telegram，而是 Owner 讀 audit matrix 時把局部 PASS 當成 evidence chain 可繼續開發。

  QA 判定：

  - market_theme_confirmed_evidence 仍缺 writer / ingestion / backfill / RLS read-only role / production data smoke。
  - Tech 已在殘留風險列出此缺口，但 CHANGELOG 前段「多個 fail-closed guard 已存在」可能被快速閱讀成整體可恢復。
  - 因此本輪只能作為 audit 條件通過，不能作為恢復 evidence chain 開發的綠燈。

  另有文件誤讀風險：

  - 原始 TASK.md 內有兩份相近任務卡串接，且第 173 行出現 `產品代碼# TASK` 連在同一行；Architect 收口時已清理為單一任務卡。

  ## 質疑與反證

  Tech 未覆蓋的補充反證：

  - inline 建構 runtime-only provider，結果 confirmed=False、source_status=missing-source，summary 明確為 production 來源不足。
  - inline 建構 support_level=strong production row，loader 回 source-error，未轉成 confirmed。
  - inline 建構 production table 空 rows，loader 回 absent，未產生 confirmed。

  對 Tech PASS 的質疑：

  - PASS 只代表 audit-level 靜態鏈路與 mocked/local tests 成立，不代表 production DB 有資料、RLS 可讀、GitHub secrets 正確或 runner production smoke 通過。
  - strategy_feature_snapshots PASS 可接受，因其 writer / reader / formatter context 均存在；但缺資料時不應被解讀為策略證據充足。
  - GitHub fresh runner PASS 可接受於「runner 由 git checkout + secrets 建 config」；但不能證明 secrets 內容、RLS policy、production rows 實際可用。

  ## 未測項目

  未做，且不應在本輪擴大：

  - full pytest
  - replay / backfill dry-run
  - live Supabase read/write smoke
  - live Telegram delivery
  - production RLS / read-only role 驗證
  - production table row freshness / coverage 驗證
  - writer / ingestion / backfill 實作驗收

  ## QA 結論

  conditional pass

  理由：

  - 產品代碼、測試、SQL、runner 無 diff；可吸收 diff 僅 CHANGELOG.md。
  - Tech matrix 的核心 fail-closed / fake fallback 正向結論，在 audit 範圍內可由源碼、局部測試與 QA inline 反證支持。
  - TASK.md 原有重複任務卡與格式串接瑕疵，Architect 收口時已清理為單一任務卡；CHANGELOG.md 對 git status / 零 diff 的敘述也已改為交付文件 diff 與產品零 diff 分開表述。
  - 更重要的是，market_theme_confirmed_evidence 端到端仍未完成；本輪不能被吸收成「可繼續 evidence chain 開發」，只能吸收成「已完成 integration audit，後續需另開 writer / ingestion / RLS / production smoke 任務」。
