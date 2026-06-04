# QA_REPORT: v20.4.37 generate() 報文手機閱讀一致性修復

  ## 測試範圍

  本輪任務尺寸為 normal_patch、QA level L2。驗收聚焦使用者可見 Telegram final message-list / summary formatter，不擴成 full pytest、DB、write path、backfill 或 live Telegram。

  讀取與比對：

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

  - 仍有上述 4 個 tracked modified file。
  - TASK.md、QA_REPORT.md 無 diff；上一輪 conditional 指出的 CHANGELOG 列 TASK.md 但 QA worktree 無 TASK diff 問題已移除。

  執行驗證：

  - pytest tests/test_generator_report.py -k 'v20_4_37 or 0604_v20_4_36_mobile_readability or single_backtest or unheld_funnel_hides_zero_count_buckets or evidence_sample_count' -q：4 passed。
  - py_compile core/generator.py presentation/report.py tests/test_generator_report.py：passed。第一次未設 PYTHONPYCACHEPREFIX 時被 sandbox 擋寫 macOS cache，改用 .qa_tmp/pycache 後通過。
  - QA 補充 final message-list 手機讀序 parser：passed，打到 official formatTelegramMessages replay 產物。

  ## 風險預算與停止條件

  本輪最值得抓的風險：

  1. 首屏未持倉總數與子分類、漏斗、詳情索引不同源，手機第一屏仍誤讀。
     驗證：解析 final message-list 的市場行、未持倉漏斗行、詳情索引、未持倉卡片標題。
     停止條件：未持倉 8 != 不可追高觀察 1 + 僅追蹤 5 + 淘汰 2 或任一區塊分類缺漏。
  2. 今日已買文案仍出現舊 風控中，造成今日買入與持倉風控口徑混淆。
     驗證：首屏 market line 必須為 今日已買 3（已風控 2/觀察 1），且不含 風控中。
  3. 回測摘要仍把建準、緯創聚合成同一行，或普通 observe 歷史噪音仍刷屏。
     驗證：final rendered text 不含 回測（建準、緯創）；含單檔 回測（建準）：、回測（緯創）：；修復股卡片不含 修復中｜連續觀察 1 天｜權重 +1。

  停止條件未觸發。

  ## 關聯風險掃描

  TASK.md、CHANGELOG.md、git diff 一致：本輪是 v20.4.37 報文 formatter/message-list 修復，不是清理、瘦身或 refactor 任務，因此不適用 path / claim / evidence / risk / action 清理證據表。

  版本檢查：

  - core/generator.py 的 VERSION = "v20.4.37"。
  - official replay summary 含 【06/04 盤中｜v20.4.37】。
  - core/generator.py、presentation/report.py 未殘留 v20.4.36、風控中、回測（建準、緯創）。

  未見 DB schema/write、RR 公式、strategy decision 相關 diff。

  ## 跨區塊語意一致性

  QA 補充 parser 從 official formatTelegramMessages final message-list 讀到：

  - 首屏 market line：
    市場：進攻偏熱 R3｜執行動作 2（停損/減碼）｜今日已買 3（已風控 2/觀察 1）｜持倉風控 3｜未持倉 8（不可追高觀察1/僅追蹤5/淘汰2）
  - 漏斗：
    未持倉 8｜不可追高觀察 1（不可買）｜僅追蹤 5（等冷卻3/等RR修復1/等量能1）｜淘汰 2
  - 詳情索引：
    📎 詳情索引：持倉 聯電、華邦電、仁寶｜交易執行 2｜不可追高觀察 1｜僅追蹤 5｜淘汰 2
  - 未持倉卡片中 不可追高觀察 卡片數為 1，且為 【建準 2421】👀 不可追高觀察。

  合計一致：8 = 1 + 5 + 2。首屏、漏斗、詳情索引、卡片分類一致。

  ## 使用者誤讀風險

  手機第一屏不再把 不可追高觀察 1 藏到漏斗才出現；首屏括號已直接顯示。

  今日買入不再裸露 風控中 舊口徑；改成 今日已買 3（已風控 2/觀察 1），能追溯今日買入中哪些已進風控、哪些仍觀察。

  回測摘要改為單檔行，避免把建準與緯創讀成同一檔或同一結論。

  ## 失敗標本反證

  TASK 要求使用 Owner v20.4.36 generate 報文等價 replay artifact，並打到 actual generate 或 official formatTelegramMessages final message-list。Tech 新增的 official replay 覆蓋 failure shape；QA 補充 parser 直接解析該
  final message-list 的手機閱讀順序。

  反證結果：

  - header 為 v20.4.37。
  - 首屏、漏斗、索引、卡片分類一致。
  - 不含舊 風控中 market line。
  - 不含普通 observe 歷史噪音 修復中｜連續觀察 1 天｜權重 +1。
  - 不含 回測（建準、緯創） 聚合。
  - 保留單檔 回測（建準）： 與 回測（緯創）：。

  ## 質疑與反證

  質疑：首屏用了新 _prepare_count_parts 後，是否只修首屏、不修漏斗與索引？
  反證：QA parser 同時讀 market line、funnel line、detail index、unheld card title，數字與分類一致。

  質疑：Tech 測試是否只驗自己新增斷言？
  反證：QA 補了獨立 parser，按手機閱讀順序解析 final message-list，而不是只重跑單一 assert。

  質疑：回測不聚合是否只在 helper 層成立？
  反證：final rendered message-list 同時出現單檔建準與緯創回測，不出現聚合行。

  ## 未測項目

  - 未跑 full pytest；符合 normal_patch/L2 風險預算，且 CHANGELOG 已揭露 legacy generator tests 仍有舊契約失敗。
  - 未驗 production runner artifact。
  - 未跑 live Telegram。
  - 未驗 DB read/write、backfill、schema、RLS、grant、policy、role。
  - 未驗即時 generate() production source 輸出的最新行情分類；本輪已用 official formatTelegramMessages final message-list replay 覆蓋 TASK 要求層級。

  ## QA 結論

  通過
