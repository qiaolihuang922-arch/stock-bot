# QA_REPORT:

  ## 測試範圍

  本輪判定為 normal_patch / L2，驗證範圍控制在 Telegram formatter、notifier consumer、market/theme evidence 文案與策略 smoke；未擴成 full pytest / replay / backfill。

  可吸收候選 diff：

  - core/generator.py
  - core/market_theme_evidence.py
  - tests/test_generator_report.py
  - tests/test_market_theme_evidence.py
  - tests/test_notifier.py
  - CHANGELOG.md

  worktree 殘留：git status --short 只顯示上述 6 個 tracked modified files，未見額外 untracked 測試產物；不建議整包合併超出上述 diff。

  已執行：

  - /usr/bin/arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py -k "v20_2_4_r3_hot"：2 passed
  - /usr/bin/arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py -k "v20_2_4" tests/test_market_theme_evidence.py tests/test_notifier.py -k "v20_2_4 or market_theme or notifier"：19 passed
  - /usr/bin/arch -arm64 .venv/bin/python -m pytest tests/test_signal_validator.py tests/test_analysis_engine.py -q：39 passed
  - git diff --check：通過
  - QA 另補 direct fixture：混合隱藏狀態輸出 另 3 檔：過熱降溫 1、突破回測 2，見詳情，未輸出誤導的 同狀態。

  ## 風險預算與停止條件

  本輪最值得抓的風險：

  1. 強勢準備超過 3 檔時，hidden overflow 把跨狀態誤寫成 同狀態。
      - 驗證：既有測試 + QA direct mixed fixture。
      - 結果：跨狀態 hidden 已按分類數量輸出；同狀態 hidden 才保留 同狀態。
  2. evidence absent 被 Owner 手機誤讀成否定外部市場強勢。
      - 驗證：summary 實際輸出不含 市場 / 題材證據：absent、市場沒有證據、題材不存在，改為內部結構化證據未啟用。
      - 結果：通過。
  3. 準備層被誤讀成可買。
      - 驗證：summary / 漏斗 / 詳情卡檢查 可買 0，準備卡使用 不可追高、不可買、待觸發。
      - 結果：通過。

  停止條件已達：header v20.2.4、R3 強勢準備層、不可買語意、summary/funnel/detail 計數、notifier consumer、策略 smoke、diff 邊界均完成。

  ## 關聯風險掃描

  git diff --name-only 未出現 DB schema、watchlist、live Telegram、Supabase write、replay/backfill、持倉停利 dedupe 相關檔案。

  core/generator.py 的改動集中在 formatter 顯示分類與 message 組裝；strong_prepare_bucket() / unheld_funnel_state(..., market_mode="進攻偏熱") 只改未持倉顯示分層，未改 BUY decision / action threshold。策略 smoke tests/
  test_signal_validator.py + tests/test_analysis_engine.py 39 passed，未見策略判斷回退。

  ## 跨區塊語意一致性

  已核對 Owner 手機閱讀順序的實際 summary：

  - Header 顯示 v20.2.4。
  - 今日結論仍是 交易執行：無新增下單 / 無有效進場，沒有把準備層包裝成買入。
  - 強勢準備區最多列 3 檔明細，overflow 按 hidden 分類數量輸出。
  - 漏斗顯示 可買 0｜可準備 N（不可買）｜僅追蹤 N｜淘汰 N。
  - 詳情卡可追溯到 可準備｜漲停鎖價 / 過熱降溫 / 突破回測，買點行明確是不可追高、不可買或待觸發。

  注意：詳情索引仍使用聚合詞 未持倉追蹤，但同一 summary 內的漏斗明確拆出 可準備 + 僅追蹤，本輪不視為阻塞。

  ## 使用者誤讀風險

  未發現會讓 Owner 誤判買入、追高或加碼的輸出。準備層標題是 強勢準備，卡片買點不是 可買，並包含 不可追高 / 不可買 / 待觸發。

  evidence absent 文案已限定為內部資料狀態：內部結構化證據未啟用、不代表外部市場不強，沒有否定外部盤面強勢。

  ## 質疑與反證

  主動反證：

  - 若 hidden items 全部同一狀態，輸出 另 N 檔同狀態見詳情 是合理且不違反本輪要求。
  - 若 hidden items 跨 過熱降溫 / 突破回測，QA direct fixture 驗證會輸出分類數量，不再混桶。
  - 可準備股票仍不進 pending_trade_items，執行區沒有出現新增下單項。
  - notifier 測試確認最後一則 formatter summary header 維持 v20.2.4。
  - 策略 smoke 通過，且 diff 未碰策略 threshold / DB / watchlist / live/backfill / 持倉停利 dedupe。

  ## 未測項目

  未跑 full pytest、正式 replay/backfill、live Telegram delivery、live Supabase write；符合本輪 normal_patch / L2 與 Architect 指令。未驗真實外部新聞或題材 provider，因 TASK 明確非目標。

  ## QA 結論

  通過
