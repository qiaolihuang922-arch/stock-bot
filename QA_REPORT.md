# QA_REPORT:

  ## 測試範圍

  - 依據：TASK.md、CHANGELOG.md、git diff。
  - 本輪候選 diff：
      - core/generator.py
      - tests/test_generator_report.py
      - CHANGELOG.md
  - worktree 狀態：目前只有上述 3 個 tracked modified files；未看到 untracked 殘留。Architect 不應整包合併，只吸收上述候選 diff。
  - 本輪不是清理 / 瘦身 / refactor 任務，path / claim / evidence / risk / action 證據表不適用。
  - 實測命令：
      - arch -arm64 .venv/bin/python -c '... pytest.main(["tests/test_generator_report.py", "tests/test_notifier.py", "-q"])'
      - 結果：37 passed, 21 warnings
  - QA 額外補測：
      - 自建完整 summary snippet：5 檔持倉、7 檔未持倉，其中 可準備 1 + 等冷卻 2 + 等回測 1 + 等RR修復 1 + 等量能 1 + 淘汰 1。
      - 結果 message list 仍為 3 則；summary 漏斗輸出為：
          - 未持倉總數 7 檔
          - 可買 0｜可準備 1（不可買）｜僅追蹤 5｜淘汰 1
          - 其中僅追蹤 5 檔拆分：等冷卻 2、等回測 1、等RR修復 1、等量能 1
          - 非執行追蹤合計 6 檔（可準備 + 僅追蹤）
      - 未出現舊式 僅追蹤 N｜等冷卻... 或 不可買追蹤 N｜可準備... 同層可誤加格式。

  ## 關聯風險掃描

  - 直接消費者 formatTelegramSummary() 會在 summary 中插入 format_unheld_funnel()，位置仍在明日執行清單後、詳情索引前。
  - 直接消費者 formatTelegramMessages() 外層 message list 未改，仍依序回傳：持倉標的、未持倉標的、summary。
  - services/notifier.send_many() 路徑以 tests/test_notifier.py 覆蓋，仍可消費 list 並只把 reply markup 放最後一則。
  - unheld_tracking_count() 現在把 等冷卻 納入追蹤數；與 detail index 的 未持倉追蹤、今日結論、執行清單一致。
  - 風險點：等冷卻 從原本併入 等回測 改為獨立排序與漏斗顯示，是使用者可見 formatter 行為；但 TASK 明確要求不得把冷卻顯示成回測，故此變更可接受，未見策略 decision / DB / payload 外層改動。

  ## 跨區塊語意一致性

  - Owner 手機閱讀順序檢查：
      - 第一眼 summary 今日結論仍先講持倉優先或可買狀態。
      - 明日執行清單仍先列持倉與可買項；不可買追蹤不列入執行。
      - 接著看到未持倉漏斗，先給 未持倉總數 7 檔，再給同層母集合，最後給 其中僅追蹤 拆分。
      - 詳情索引顯示 持倉 5｜執行 5｜未持倉追蹤 6｜淘汰 1，與 QA 額外案例的 可準備 1 + 僅追蹤 5 = 非執行追蹤 6 對齊。
  - Tech 第二輪重點 可準備 > 0：已反證 其中 的母集合是 僅追蹤 5，不是 非執行追蹤 6，避免把可準備混進冷卻 / 回測 / RR / 量能拆分。
  - TASK 指定 12 檔 / 持倉 5 / 未持倉 7 案例：測試覆蓋 未持倉總數 7、僅追蹤 6、淘汰 1，未持倉母集合合計為 7。

  ## 使用者誤讀風險

  - 舊風險 僅追蹤 7 + 冷卻 3 + 回測 2... 同層加總已移除。
  - 新格式雖仍有多個數字，但語意改為：
      - 未持倉總數 是總量。
      - 可買 / 可準備 / 僅追蹤 / 淘汰 是同層母集合。
      - 其中僅追蹤 只拆僅追蹤，不拆可準備或淘汰。
      - 非執行追蹤合計 明確標註是 可準備 + 僅追蹤。
  - 未發現會把不可買、等待、僅追蹤誤讀成可買或必須執行的文案；可準備 保留 （不可買）。

  ## 質疑與反證

  - PM 是否漏需求：TASK 有直接消費者、輸出契約、手機閱讀路徑與 12/5/7 fixture，足以驗收。
  - Tech 是否漏同步：已同步 summary formatter 測試，並重跑 notifier 消費路徑；message list 外層結構未變。
  - 測試是否能證明沒有破壞直接消費者：tests/test_generator_report.py + tests/test_notifier.py 通過，QA 額外 snippet 驗證完整 summary 與 message count。
  - QA 主動反證：
      - 補了 Tech 第二輪核心邊界 可準備 > 0 的完整手機 summary 案例。
      - 檢查 未持倉總數 7、母集合 0+1+5+1=7、追蹤合計 1+5=6、詳情索引 未持倉追蹤 6 四處一致。
      - 檢查舊式可誤加同層格式未出現。

  ## 未測項目

  - 未跑 full pytest；本輪 QA 分級為 L1，且改動集中在 Telegram formatter 與 notifier 消費契約，局部測試可接受。
  - 未做 live Telegram delivery、live Supabase write、正式 replay/backfill；TASK 明確禁止。
  - 未測 DB payload、策略輸出、watchlist 實際清單變更；git diff 未觸及相關模組，且本輪非目標。

  ## QA 結論

  通過
