# QA_REPORT: telegram-breakout-distance-always-visible-v20.2.1

  ## 測試範圍

  - 任務尺寸 / QA level：tiny_patch / L1，本輪只驗 Telegram formatter 卡片盤面行、版本 header、notifier direct consumer；未擴大到 full pytest、replay、backfill。
  - 讀取文件：TASK.md、CHANGELOG.md、git status --short、git diff --stat/name-only、core/generator.py 與相關測試 diff。
  - 可吸收 diff：
      - core/generator.py
      - tests/test_generator_report.py
      - tests/test_notifier.py
      - tests/test_market_theme_evidence.py
      - CHANGELOG.md
  - worktree 殘留：git status --short 只顯示上述 5 個修改檔；未看到本輪外的殘留 diff，不建議整包以外合併。

  ## 風險預算與停止條件

  - 風險 1：CHANGELOG.md 與實際 diff / status 不一致。驗證：比對 changelog、diff stat、diff name-only、實作內容；結果一致。
  - 風險 2：有突破距離資料但卡片盤面行仍漏顯，或持倉 / 未持倉規則不一致。驗證：讀 card_breakout_distance() 與兩個 card formatter，並跑測試；結果通過。
  - 風險 3：缺距離資料時輸出假距離，或 notifier message list / 最後 summary header 被破壞。驗證：既有測試加 QA smoke；結果通過。
  - 停止條件：formatter / snapshot / notifier direct consumer 通過，且無策略、DB、watchlist、live、backfill diff；已達成。

  ## 關聯風險掃描

  - core/generator.py 僅升 VERSION = "v20.2.1"，新增 card_breakout_distance(data)，並讓持倉 / 未持倉卡片共用距離讀取。
  - card_breakout_distance() 對 None、缺 key、空字串 fallback / omit，未把缺資料改成 0%、None% 或空括號。
  - git diff --name-only -- services/analysis.py core/watchlist.py db migrations scripts 無輸出。
  - git diff --name-only -- '*backfill*' '*replay*' '*supabase*' '*watchlist*' 無輸出。
  - 未看到策略 decision、突破門檻、DB schema、watchlist、live Telegram、replay/backfill 相關 diff。
  - 本輪不是清理 / 瘦身 / refactor 任務，path / claim / evidence / risk / action 證據表要求不適用。

  ## 跨區塊語意一致性

  - 版本：core/generator.py 為 v20.2.1，tests/test_generator_report.py、tests/test_notifier.py、tests/test_market_theme_evidence.py header 期望均同步到 v20.2.1。
  - 卡片語意：持倉與未持倉皆使用同一 card_breakout_distance()，盤面行經 compact_market_line(result, dist) 顯示同一套已突破 / 臨界突破 / 接近突破 / 遠離突破文字。
  - message list / notifier：send_many() 仍保留最後一則 summary 原文，未改 payload shape 或 reply markup 行為。

  ## 使用者誤讀風險

  - Owner 手機閱讀順序：summary 最後一則仍帶 【05/28 盤中｜v20.2.1】；往上看持倉 / 未持倉卡片時，盤面行可直接看到突破狀態與距離。
  - 有距離資料時，已突破、臨界突破、接近突破、遠離突破都保留括號距離，不需 Owner 自行推算。
  - 缺距離資料時，本輪沿用 TASK 允許的「省略距離」路徑；QA smoke 確認未輸出假 0%、None%、空括號。若未來要強制顯示「距離缺資料」，需另開 PM 契約，不是本輪阻塞。

  ## 質疑與反證

  - 反證 Tech 自檢句：CHANGELOG.md 宣稱的 72 passed, 21 warnings 與實跑結果一致。
  - 反證「只測產出函式」不足：QA 另跑 direct consumer smoke，組合持倉卡、未持倉卡、缺距離卡與 summary，經 notifier.send_many() mock 驗證最後一則仍是 v20.2.1 summary。
  - 反證缺資料造假：QA smoke 中完全缺 data.breakout_distance 與 result.breakout_distance 時，卡片沒有 （0%）、None%、（）。
  - 反證範圍外風險：diff path 掃描未發現策略、DB、watchlist、Supabase、replay/backfill 變更。

  執行命令：

  - arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py tests/test_notifier.py tests/test_market_theme_evidence.py
      - 結果：72 passed, 21 warnings
  - git diff --check
      - 結果：通過，無 whitespace error。
  - QA 補充 smoke：
      - 結果：qa_smoke_passed: cards keep distance, missing data has no fake distance, notifier sends v20.2.1 summary last

  ## 未測項目

  - 未跑 full pytest，符合 tiny_patch / L1 停止條件。
  - 未跑 replay / backfill dry-run。
  - 未做 live Telegram delivery。
  - 未做 live Supabase write。
  - 未驗 DB schema / migration，因本輪無相關 diff。

  ## QA 結論

  通過
