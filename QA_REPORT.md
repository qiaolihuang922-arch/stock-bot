# QA_REPORT:

  ## 測試範圍

  - 任務尺寸 / QA：risk_patch / L3；範圍限定在 TASK.md 指定的使用者可見報文、同層 06/03 message-list replay、targeted tests、compile、diff check；未擴大到 production smoke / live Telegram / backfill。
  - 已核對：TASK.md、CHANGELOG.md、git diff --name-only、core/generator.py、presentation/report.py、services/analysis.py、相關測試 diff。
  - 可吸收 diff：CHANGELOG.md、core/generator.py、presentation/report.py、services/analysis.py、tests/test_analysis_engine.py、tests/test_generator_report.py、tests/test_market_theme_evidence.py、tests/
    test_strategy_evidence.py。
  - worktree 殘留：上述 8 個 tracked modified files；未見 services/strategy_evidence.py modified。

  ## 風險預算與停止條件

  - 風險 1：06/03 手機閱讀順序仍有跨區塊矛盾，例如聯電 summary / 持倉卡主行動不同、技嘉 RR 數值外漏、光寶科出現 不買｜進場。驗證：單一 06/03 message-list replay。停止條件：任一矛盾出現即 blocked。
  - 風險 2：D1 防抖只改 title 文案但未守住分類契約，導致單次或 breakout_distance > 1% 仍翻可買。驗證：既有單卡測試 + QA 額外 consumer probe。停止條件：保守側未維持或出現進場語意即 blocked。
  - 風險 3：TASK / CHANGELOG / diff / version 不一致。驗證：diff 檔案清單、VERSION 搜尋、services/strategy_evidence.py 未修改確認。停止條件：版本殘留、CHANGELOG 列錯實際檔案、或 diff 含禁止修改檔即 blocked。

  ## 關聯風險掃描

  - CHANGELOG.md 宣告版本 v20.4.33，實際 core/generator.py 為 VERSION = "v20.4.33"；產品與測試範圍內未搜尋到舊版 v20.4.32 殘留，測試名稱 / TASK 歷史標本語意除外。
  - services/strategy_evidence.py 未出現在 modified list；符合 Architect 指令與 CHANGELOG「未修改」。
  - git diff --check：passed。
  - py_compile 使用 PYTHONPYCACHEPREFIX=.qa_tmp/pycache：passed。
  - targeted suite：240 passed，只有既有第三方 deprecation warnings。

  ## 跨區塊語意一致性

  - 06/03 replay passed：聯電卡片為 減碼，summary 也含 聯電｜-3.86%｜減碼，未再把 新倉風控觀察 當主行動。
  - 技嘉 replay passed：等冷卻 / 過熱觀察卡片顯示 RR -（過熱），未顯示 RR 0.21。
  - 簡報原因行 replay passed：只有一行原因，不逐檔串接，且未出現 ； 分隔的逐檔原因。
  - 未持倉回測降噪 replay passed：未逐卡輸出 回測：不可用、回測：-、樣本不足（有效樣本3）。
  - 盤中 / 盤後共用降噪由 targeted report tests 覆蓋，未另跑 full replay matrix。

  ## 使用者誤讀風險

  - 主要誤讀路徑「⛔ 不買｜進場」已被 replay 和額外 probe 反證：整份 06/03 message list 不含 不買｜進場，光寶科顯示 不買｜前態待確認。
  - Summary 手機閱讀順序未再把無有效新倉寫成推薦語氣；相關 targeted tests 保持 新倉：無有效進場。
  - 殘留風險：本輪 replay 是等價 message-list fixture，不是 live Telegram 實機截圖；依 Architect 指令不要求 live delivery。

  ## 失敗標本反證

  - 命令：arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py::GeneratorReportTest::test_0603_v20_4_32_failure_specimen_message_list_replay
  - 結果：1 passed。
  - 覆蓋 Owner 06/03 等價標本的同層 message-list：聯電減碼、技嘉過熱 RR 隱藏、光寶科 D1 防抖、原因行精簡、未持倉回測降噪、版本 v20.4.33。

  ## 質疑與反證

  - QA 額外 probe：previous_state=weak、consecutive_buy_signals=2 但 breakout_distance=1.2，結果仍為 淘汰，卡片含 前態待確認，不含 可買｜ / 不買｜進場。這補到 Tech 單次防抖以外的 breakout distance 邊界。
  - 反證結論：D1 防抖不是只修掉字串；分類仍維持保守側，符合「連續確認且 breakout_distance <= 1% 才允許可買」契約。

  ## 未測項目

  - 未跑 live Telegram delivery、production write、正式 backfill。
  - 未跑 production smoke / read-only DB artifact；Architect 明確指示本輪不要求。
  - 未跑 full pytest；本輪按 L3 風險點跑 targeted suite + replay + 額外 probe。

  ## QA 結論

  通過
