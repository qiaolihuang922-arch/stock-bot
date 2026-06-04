# QA_REPORT:

  ## 測試範圍

  本輪任務尺寸：normal_patch，QA level：L2。驗收範圍限定在 v20.4.38 使用者可見 Telegram final message-list / official formatTelegramMessages，未擴成 full pytest、production replay、DB/write/live Telegram。

  讀取並比對：

  - TASK.md
  - CHANGELOG.md
  - git diff
  - core/generator.py
  - presentation/report.py
  - tests/test_generator_report.py

  可吸收 diff：

  - CHANGELOG.md
  - core/generator.py
  - presentation/report.py
  - tests/test_generator_report.py

  worktree 殘留：

  - git status --short 僅顯示上述 4 個 modified tracked files。
  - 未發現額外 untracked 測試產物；QA 只使用 .qa_tmp/ 作暫存。

  ## 風險預算與停止條件

  本輪最值得抓的風險：

  1. final header 未實際升到 v20.4.38。
      - 驗證：official formatter replay 與 focused tests 檢查 header。
      - 停止條件：header 仍是 v20.4.37 或版本來源不可確認。
  2. 等RR修復｜RR不足 卡片仍顯示 證據：資料不足，造成資料源缺失誤讀。
      - 驗證：光寶科卡片連讀，檢查狀態與數據行。
      - 停止條件：同一卡片仍含 證據：資料不足 或狀態被改成可買/不可追高來掩蓋。
  3. summary 仍把光寶科列為 回測（光寶科），讓手機閱讀誤以為接近可買。
      - 驗證：按手機閱讀順序檢查 summary 再讀未持倉卡片。
      - 停止條件：summary 出現 回測（光寶科） 且未明確標成僅追蹤/等RR修復。

  ## 關聯風險掃描

  TASK / CHANGELOG / git diff 一致：任務為 v20.4.38 RR不足 / 等RR修復可讀性修復，修改檔案清單與實際 diff 一致；上一輪 conditional 提到的 TASK.md 修改檔案不一致已不存在。

  程式 diff 符合邊界：

  - core/generator.py：VERSION 升為 v20.4.38；format_backtest_groups() 依未持倉狀態過濾 summary 回測。
  - presentation/report.py：只針對 hidden score reason 為 RR不足 時改顯示 原因：RR不足，等待RR修復。
  - 未見 DB schema/write、RR 公式、strategy decision、live Telegram、交易排序改動。

  注意：format_backtest_groups() 白名單為 可買 / 趨勢延續 / 可準備。TASK 文字提到可買 / 不可追高等實際候選語境；本輪指定硬驗收要求「建準候選回測保留」，已由測試證明建準保留。若 Owner 後續要求所有不可追高觀察都保留回測，
  需要另開契約澄清，不阻塞本輪光寶科修復。

  ## 跨區塊語意一致性

  驗證命令：

  - pytest tests/test_generator_report.py -k 'v20_4_38_rr_wait_card_reason_and_backtest_summary_readability or 0604_v20_4_37_generate_mobile_consistency_message_list_replay or
    v20_4_37_single_backtest_lines_are_not_aggregated or v20_4_36_non_actionable_unheld_hides_score_numbers' -q：4 passed。
  - pytest tests/test_generator_report.py -k 'v20_4_38_rr_wait_card_reason_and_backtest_summary_readability' -q：1 passed。
  - py_compile core/generator.py presentation/report.py tests/test_generator_report.py && git diff --check：passed。
  - QA 自補 official formatter 反證：passed。

  反證結果：

  - summary header 含 【06/04 盤中｜v20.4.38】。
  - summary 保留 回測（建準）。
  - summary 不含 回測（光寶科）。
  - 光寶科卡片仍為 【光寶科 2301】👀 等RR修復｜RR不足。
  - 光寶科數據行為 數據：RR 0.98｜不適用（RR不足）｜原因：RR不足，等待RR修復｜V 0.86x。
  - 光寶科卡片不含 證據：資料不足。
  - QA 自補負面案例確認非 RR 低量卡片仍保留 證據：量能不適用，修正不是全域替換 evidence 文案。

  ## 使用者誤讀風險

  按手機閱讀順序檢查：

  1. 先讀 summary：建準可見 回測（建準），光寶科不出現在回測摘要。
  2. 再讀未持倉卡片：光寶科狀態是 等RR修復｜RR不足。
  3. 同一卡片數據行明確寫 原因：RR不足，等待RR修復，不再把 RR 不足表述成資料源缺失。

  結論：本輪 Owner 指出的兩個誤讀路徑已被 official formatter replay 覆蓋。

  ## 質疑與反證

  主動質疑：是否只是把所有不可行動 evidence 全域改成 RR不足原因？

  反證：QA 自補 official formatter 同時放入 RR不足光寶科與非 RR 低量標的。結果光寶科顯示 RR 原因，低量標的仍顯示 evidence 類文案 證據：量能不適用，未發現全域替換。

  主動質疑：是否只驗 helper 而未打到 final message-list？

  反證：新增與 QA 自補驗證都走 generator.formatTelegramMessages(...)，取得 summary / unheld message / card block，不是 helper-only。

  ## 未測項目

  - 未跑 full pytest；符合 normal_patch / L2 風險預算。
  - 未跑 production runner artifact。
  - 未跑 actual live Telegram。
  - 未做 DB read/write/backfill。
  - 未驗 RR 數值隨即時價變動的完整 generate production output；本輪驗證的是 formatter 語意與 summary 納入規則。

  ## QA 結論

  通過
