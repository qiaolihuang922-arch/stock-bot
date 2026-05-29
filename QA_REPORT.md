# QA_REPORT:

  ## 測試範圍

  任務尺寸：risk_patch，QA level：L2。未擴成 full pytest / replay / backfill。

  讀取與核對：

  - TASK.md
  - CHANGELOG.md
  - git status --short
  - git diff --stat
  - git diff -- core/generator.py tests/test_generator_report.py tests/test_market_theme_evidence.py tests/test_notifier.py CHANGELOG.md

  可吸收 diff：

  - CHANGELOG.md
  - core/generator.py
  - tests/test_generator_report.py
  - tests/test_market_theme_evidence.py
  - tests/test_notifier.py

  worktree 殘留：

  - 未發現超出上述清單的 tracked diff。
  - CHANGELOG.md 已列自身，上一輪「CHANGELOG 未列自身」阻塞點已解除。

  執行命令：

  - git diff --check：通過
  - arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py -k "v20_2_3 or intraday_v20_0_10_execution_contract" tests/test_notifier.py tests/test_market_theme_evidence.py：4 passed
  - arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py tests/test_notifier.py tests/test_market_theme_evidence.py：76 passed
  - arch -arm64 .venv/bin/python -m pytest tests/test_analysis_engine.py -k "same_day_profit_taken or overheat or stop or take_profit"：8 passed

  ## 風險預算與停止條件

  本輪最值得抓的 3 個風險：

  1. completed DB execution 仍讓 Owner 誤以為今日要再賣一次。
     驗證：英業達 db_execution shares_delta=-75，原建議 56，檢查 summary / 持倉卡 / 風控檢查。
     結果：顯示 今日 賣 75股、第二段停利後觀察、今日已賣 75 股｜剩餘 225 股｜第二段已執行；未出現 今日 無、無本次建議 56、本次建議 56 股。
  2. partial local execution 仍顯示完整原建議 56 股。
     驗證：local_executions shares=20，原建議 56。
     結果：顯示 今日 賣 20股、第二段停利剩餘建議 36 股｜今日已賣 20 股｜原建議 56 股｜剩餘持倉 280 股；未出現 今日 無 或 本次建議 56 股 作為完整待執行建議。
  3. unexecuted 被誤去重，導致真正第二段停利消失。
     驗證：無 DB / local execution。
     結果：仍顯示 第二段停利｜本次建議 56 股｜剩餘 300 股，符合 TASK 未執行案例。

  停止條件：

  - 三個 fixture 已覆蓋 completed / partial / unexecuted。
  - header 已核對為 v20.2.3。
  - touched tests 與策略 smoke 通過。
  - diff 未觸及 DB schema、watchlist、live/backfill 入口或策略門檻檔案。

  ## 關聯風險掃描

  - core/generator.py 版本常量由 v20.2.2 升為 v20.2.3，相關 formatter / notifier 測試已同步。
  - diff 未包含 DB schema、migration、Supabase write path、watchlist、backfill script。
  - strategy smoke 測試通過；未看到 RR、過熱、漲停不追、停損停利策略門檻被改。
  - CHANGELOG.md 與 diff 一致：已列出自身、core/generator.py 與三個測試檔。

  ## 跨區塊語意一致性

  Owner 手機閱讀順序反證：

  completed：

  - header：【05/29 盤中｜v20.2.3】
  - 持倉卡：【英業達 2356】📌 第二段停利後觀察，今日 賣 75股
  - 決策：今日已賣 75 股｜剩餘 225 股｜第二段已執行
  - summary 今日執行：英業達｜已執行｜今日已賣 75 股｜剩餘 225 股｜第二段已執行
  - 風控檢查：英業達｜第二段停利後觀察｜今日已賣 75 股｜剩餘 225 股｜第二段已執行
  - 未出現互相矛盾的完整待賣 56 股。

  partial：

  - 持倉卡：第二段停利剩餘建議，今日 賣 20股
  - summary / 風控檢查同樣顯示剩餘建議 36 股、今日已賣 20 股、原建議 56 股。
  - 沒有把 56 股重新包裝成「本次建議 56 股」。

  unexecuted：

  - 持倉卡、summary、風控檢查都保留 第二段停利｜本次建議 56 股｜剩餘 300 股。
  - 今日 無 只出現在未執行持倉卡，未污染 completed / partial。

  ## 使用者誤讀風險

  未發現會讓 Owner 在 completed 案例重複賣出的文案。completed 第一眼看到的是「已執行 / 後觀察」，不是可執行第二段停利。

  partial 仍有 原建議 56 股，但上下文同列 剩餘建議 36 股｜今日已賣 20 股，語意可接受；不會被讀成完整再賣 56 股。

  unexecuted 保留完整建議，符合 TASK，不視為噪音或誤導。

  ## 質疑與反證

  主動質疑 1：Tech 是否只修持倉卡，漏掉 summary / 風控檢查。
  反證：獨立 fixture 實際輸出顯示 completed / partial 的 summary 與風控檢查均同步同一 action 與股數。

  主動質疑 2：DB execution 與 local execution 來源不同，是否只覆蓋其中一種。
  反證：completed 用 db_execution，partial 用 local_executions，兩者皆通過手機順序檢查。

  主動質疑 3：修 completed / partial 後，未執行第二段是否被錯誤吞掉。
  反證：unexecuted 仍顯示 第二段停利 / 本次建議 56 股 / 剩餘 300 股。

  ## 未測項目

  - 未跑 full pytest，因本輪 L2 不要求且會超出停止條件。
  - 未跑 replay / backfill dry-run。
  - 未做 live Telegram delivery。
  - 未做 live Supabase write。
  - 未驗證正式 DB execution stage 歷史資料精準分類；CHANGELOG.md 已將 execution stage 限制列為殘留風險。

  ## QA 結論

  通過
