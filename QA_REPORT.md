# QA_REPORT:

  ## 測試範圍

  - 任務尺寸 / QA 分級：risk_patch / L2。範圍收斂在 Telegram formatter、持倉主行動一致性、版本 header、直接 consumer smoke。
  - 已讀：TASK.md、CHANGELOG.md、git status --short、git diff --stat、git diff --name-only、core/generator.py 與相關測試 diff。
  - 可吸收 diff：
      - CHANGELOG.md
      - core/generator.py
      - tests/test_generator_report.py
      - tests/test_market_theme_evidence.py
      - tests/test_notifier.py
  - worktree 殘留：未看到上述以外的 modified / untracked 檔案；QA 未修改 tracked file。
  - CHANGELOG.md 與 git diff 一致：修改檔案清單已列 CHANGELOG.md，且內容改為「CHANGELOG.md 僅同步本輪交付摘要，未承載產品邏輯」，不再宣稱未直接編輯。

  ## 風險預算與停止條件

  - 風險 1：CHANGELOG / diff 不一致，造成 Architect 吸收錯誤範圍。
      - 驗證：git diff --name-only 對照 CHANGELOG.md 修改檔案。
      - 結果：一致。
  - 風險 2：Owner 手機看到同日已賣後仍像同級停利，誤以為再賣一次。
      - 驗證：直接 formatter fixture 檢查 summary / 今日交易執行 / 持倉風控檢查 / 持倉卡。
      - 結果：POST_PROFIT_WATCH 顯示「停利後觀察」，第二段停利顯示「今日已賣 / 剩餘 / 本次建議」。
  - 風險 3：版本 header 或直接 consumer 未同步。
      - 驗證：formatter header、notifier header consumer、market evidence header smoke。
      - 結果：均為 v20.2.2。
  - 停止條件：不跑 full pytest / replay / backfill / live delivery；本輪不擴到策略門檻、DB、watchlist、正式寫入。

  ## 關聯風險掃描

  - git diff --check：通過。
  - git diff --name-only：只包含 CHANGELOG、formatter 與三個直接測試檔。
  - 未見 services/analysis.py、DB / Supabase、watchlist、live Telegram、backfill 相關 diff。
  - 已跑命令：
      - arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py -k "v20_2_2"：3 passed。
      - arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py::...v20_2_2... tests/test_generator_report.py::...test_intraday_v20_0_10_execution_contract：4 passed。
      - arch -arm64 .venv/bin/python -m pytest tests/test_notifier.py tests/test_market_theme_evidence.py tests/test_analysis_engine.py -k "version_header or market_theme or profit"：23 passed。
  - pytest warnings 為既有依賴 deprecation / Python 版本警告，未影響本輪驗收。

  ## 跨區塊語意一致性

  - POST_PROFIT_WATCH 今日已賣案例：
      - 持倉卡：停利後觀察、今日 賣 112股（25%）、決策：停利後觀察，暫不加碼。
      - 今日交易執行：今日已執行停利 112 股｜成交後剩餘 188 股｜同級停利已完成。
      - 持倉風控檢查：停利後觀察｜成交後剩餘 188 股｜同級停利已完成。
      - 未再出現同級 停利 25% 作為主行動。
  - 第二段停利案例：
      - 持倉卡：第二段停利｜+30.00%。
      - 決策：第二段停利，今日已賣 112 股｜剩餘 188 股｜本次建議 47 股。
      - summary 與持倉風控檢查同樣顯示 第二段停利｜今日已賣 112 股｜剩餘 188 股｜本次建議 47 股。
      - 有觸發條件：過熱延伸再次達停利條件。

  ## 使用者誤讀風險

  - Owner 手機閱讀順序檢查：
      - 先看到 header：【05/29 盤中｜v20.2.2】。
      - 再看到今日結論：已區分「無新增下單」與「已執行 1 項不重複」。
      - 再看今日交易執行：已賣股數與剩餘股數清楚。
      - 再看持倉風控檢查 / 持倉卡：主行動與前段一致。
  - 未發現會讓 Owner 把 POST_PROFIT_WATCH 誤讀成同級再次停利的輸出。
  - 第二段停利不是裸 停利，已同行帶出今日已賣、剩餘、本次建議與觸發條件，可接受。

  ## 質疑與反證

  - 主動反證 1：檢查策略既有 POST_PROFIT_WATCH 測試，確認策略層同級已停利仍維持觀察語意，未被 formatter patch 回退。
  - 主動反證 2：檢查 notifier 直接 consumer，確認最後一則 message header 保留 v20.2.2，不是只改 formatter 單元輸出。
  - 主動反證 3：檢查第二段停利負面 / 邊界案例，確認同日已賣後若策略仍給 TAKE_PROFIT_25 且有可賣股數，輸出升級為明確 第二段停利，不是含糊的同級 停利。
  - 清理 / 瘦身 / refactor 證據表：本輪不是清理任務，不適用 path / claim / evidence / risk / action 表要求。

  ## 未測項目

  - 未跑 full pytest，符合本輪 L2 窄範圍與 Architect 指令。
  - 未跑 replay / backfill dry-run。
  - 未測 live Telegram delivery、live Supabase write。
  - 未驗 DB payload / schema / watchlist，因 diff 未觸及且 TASK 明列非目標。

  ## QA 結論

  通過
