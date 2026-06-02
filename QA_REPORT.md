# QA_REPORT:

  ## 測試範圍

  - 任務尺寸 / QA：risk_patch / L3；本輪驗證聚焦 TASK 指定第 4/5/6/7/9/12 與第 8/10/11 回歸，未擴成 production replay / backfill / live Telegram。
  - 讀取：TASK.md、CHANGELOG.md、git diff、core/generator.py、presentation/report.py、services/stock_api.py、相關 tests。
  - 可吸收 diff：core/generator.py、presentation/report.py、services/stock_api.py、tests/test_generator_report.py、tests/test_stock_api_history.py，均落在本輪契約範圍。
  - worktree 殘留：CHANGELOG.md dirty 為 handoff 文件變更；未發現與本輪 code diff 矛盾。未修改 tracked files。

  ## 風險預算與停止條件

  - 風險 1：source-missing 手機第三則仍像交易執行摘要。驗證：直接 probe _source_missing_report_messages() 第三則與全訊息。停止條件：出現 ✅ 今日盤中交易執行、無新增下單、交易執行：無新增下單。
  - 風險 2：fail-closed source 被文案或跨日記憶誤讀為已確認。驗證：legacy strategy text、cross_day_context.source_status=insufficient-data。停止條件：legacy text 被判 available，或 insufficient cross_day 產生 completed /
    confirmed。
  - 風險 3：使用者可見輸出回退成噪音或誤讀。驗證：全 0 未持倉漏斗、LAST_OHLCV stale、已突破負百分比、手機閱讀順序。停止條件：0-count 空區塊、非當日資料無提示、已突破（-xx%） 出現。

  ## 關聯風險掃描

  - TASK.md / CHANGELOG.md / git diff 一致：一致。CHANGELOG 宣告的 source-missing 空執行占位修復、stale fallback、strategy structured status、0-count 隱藏、負百分比格式化，均可在 diff 找到對應修改與測試。
  - 清理 / 瘦身 / refactor 證據表：本輪不是清理任務，不適用 path / claim / evidence / risk / action 表。
  - 測試：
      - arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py tests/test_stock_api_history.py
      - 結果：125 passed, 225 warnings
      - warnings 為既有 dependency / Python deprecation，未阻塞本輪。
  - git diff --check：通過。

  ## 跨區塊語意一致性

  - 第三則 source-missing brief 不含 ✅ 今日盤中交易執行、無新增下單、交易執行：無新增下單。
  - 全 0 未持倉漏斗不輸出：format_unheld_funnel([]) == ""，source-missing 全訊息不含 未持倉總數 0 檔 / 僅追蹤 0。
  - legacy strategy rendered text fail closed：文字版「來源可驗證」回傳 missing-source，原因含未用文字摘要反推。
  - cross_day insufficient 不確認：cross_day_ready=False、無 detail line、無 duplicate action、second take profit state 未完成。
  - LAST_OHLCV stale 有使用者可見提示：建準 使用 LAST_OHLCV 2026-05-29，非當日資料。
  - 已突破負百分比不出現：semantic_position(-21.6) 不含 -21.6 或 （-。

  ## 使用者誤讀風險

  - 按手機閱讀順序檢查 Summary / brief evidence：source-missing 路徑表達來源不足、策略樣本不納入買賣判斷，未出現交易執行空區塊。
  - stale 行情不會被讀成當日資料，summary source line 明示 LAST_OHLCV 日期與「非當日資料」。
  - 未發現 已確認 / confirmed 出現在 source-missing 第三則造成確認語氣誤讀。
  - source-missing brief 仍有兩個新倉不可行動說法：「目前沒有可行動候選」與「無有效進場」；未形成交易建議或空占位，本輪不列阻塞。

  ## 質疑與反證

  - QA 補充 Tech 未覆蓋的直接負面 probe：同時組合 source-missing 第三則、legacy strategy text、cross_day insufficient、LAST_OHLCV stale、突破負百分比。
  - 反證結果通過：未觸發本輪停止條件。
  - 未把 Tech 自檢等同 QA；另跑了直接 helper / 使用者可見文字 probe。

  ## 未測項目

  - 未跑 production smoke、replay、backfill、live Telegram，符合本輪禁止事項。
  - 未驗證 production DB source-of-truth 實際資料內容。
  - 未做全 repo pytest；本輪依 L3 但限縮在 TASK 指定輸出契約與直接消費者測試檔。

  ## QA 結論

  通過
