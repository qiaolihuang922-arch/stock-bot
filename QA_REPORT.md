# QA_REPORT:

  ## 測試範圍

  依據 TASK.md、CHANGELOG.md、git diff 驗證最新候選 diff。git status --short 顯示僅有：

  - CHANGELOG.md
  - core/generator.py
  - tests/test_generator_report.py

  本輪不是清理 / 瘦身 / refactor 任務，path / claim / evidence / risk / action 證據表不適用。

  已執行指定測試：

  - tests/test_generator_report.py tests/test_notifier.py -q
  - 結果：39 passed, 21 warnings

  額外 QA 自製 fixture：

  - 今日買入持倉 + ADD_20，同報文含 STOP_100、REDUCE_25。
  - 高分 S=5 / 極強 但 RISK_WATCH 風控優先持倉。
  - 未持倉漏斗 可準備 + 等冷卻 + 等回測 + 淘汰 拆分。
  - 結果：CUSTOM_QA_OK

  ## 關聯風險掃描

  TASK.md、CHANGELOG.md 與 diff 一致：修改集中在 Telegram formatter 與直接 formatter 測試，未見策略、DB、watchlist、replay/backfill、live delivery 變更。

  直接消費者檢查：

  - formatTelegramMessages() 外層仍回傳 position_message, unheld_message, summary_message 三段；include_detail=True 仍前置完整詳情備份。
  - tests/test_notifier.py 通過，services.notifier.send_many() 仍把 reply markup 掛到最後一則 message，message list 外層消費者未破。
  - 自製 fixture 驗證 len(messages) == 3，summary 仍在 messages[-1]。

  可吸收 diff 僅限本輪候選：

  - core/generator.py
  - tests/test_generator_report.py
  - CHANGELOG.md

  worktree 殘留：git status 未顯示其他 tracked/untracked 變更；不得把未來 worktree 其他變更整包合併。

  ## 跨區塊語意一致性

  手機閱讀順序檢查 summary 最新訊息：

  - Header 顯示 v20.0.1，符合本輪不升版契約。
  - Summary 的明日執行清單中，STOP_100 排在 REDUCE_25 前，兩者都高於今日買入 + ADD_20。
  - 今日買入 + ADD_20 在 summary、持倉卡、明日清單均為 新倉風控觀察，未出現 加碼20、加碼 20%、加碼後守警戒價。
  - 高分但風控優先持倉在 summary 為 風控觀察｜暫不加碼，持倉卡為 風控觀察，暫不加碼，未被 🔥 最強、可買、加碼 重新包裝。
  - 多檔淘汰 summary 顯示 淘汰 N 檔｜主因：...｜詳情見未持倉卡，未完整點名；未持倉卡仍保留逐檔明細。
  - 等冷卻 與 等回測 在漏斗拆分中獨立計數，未混桶。

  ## 使用者誤讀風險

  今日買入後的 ADD_20 訊號已被壓成新倉風控觀察，Owner 不會從 summary 或明日清單誤讀成加碼。

  高分風控案例仍會在持倉卡數據行顯示 S 5/5、盤面 極強，但同一卡片標題、決策、下一步均明確寫 風控觀察 / 暫不加碼，summary 也沒有把該股列成 最強 或可買；目前可接受。

  未持倉漏斗未恢復舊的一行 不可買追蹤，而是保留 未持倉總數、母集合、僅追蹤拆分、非執行追蹤合計，總數誤讀風險可控。

  ## 質疑與反證

  PM 是否漏需求：Architect 額外要求的 6 點已逐項反證，沒有發現與 TASK.md 衝突。

  Tech 是否漏同步：檢查 position_summary_action()、formatTelegramPositionCard()、holding_execution_item()、format_unheld_funnel()、rejected_trace_line()；summary、持倉卡、明日清單與未持倉卡同步一致。

  測試是否能證明直接消費者未破：除 Tech 測試外，QA 額外確認 message list 長度、summary 位置與 notifier send_many() 測試結果。

  指定清單之外風險：主動檢查高分風控卡片仍顯示 S=5/極強 是否造成可買誤讀；因同區塊主行動與 summary 都明確風控，不構成阻塞。

  ## 未測項目

  未執行 full pytest、replay/backfill dry-run、live Telegram、live Supabase write；依 TASK.md 非目標與 L2 範圍可接受。

  未驗證真實 Telegram 手機截圖；已用 message list 實際字串順序檢查 Owner 打開後的 summary、執行清單、漏斗、詳情索引語意。

  ## QA 結論

  通過
