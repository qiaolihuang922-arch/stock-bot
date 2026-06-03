# CHANGELOG:

  ## 任務尺寸與風險

  normal_patch。延續 telegram_message_noise_consistency_20260603，只修 QA blocker 與相關 snapshot expectations；未改策略 decision、RR 公式、DB schema/write、live Telegram。

  ## 修改內容

  - 修正 compact market line：未持倉拆分在有可買標的時加入可買數，例如 未持倉 2（可買1/僅追蹤0/淘汰1）。
  - 保留無可買情境的 no-buy compact style，例如 未持倉 4（僅追蹤3/淘汰1）。
  - 同步 tests/test_generator_report.py 中與新簡報降噪、短交易摘要、不可行動 RR 顯示相關的 full-file expectations。
  - 保留候選 diff 既有修復：不可行動 RR 顯示、partial + modifier=1.0 顯示 僅輔助參考、簡報冗餘行排除、交易執行短摘要與歷史 token 去重。

  ## 修改檔案

  - presentation/report.py
  - core/generator.py
  - tests/test_generator_report.py

  ## 最小改動策略

  只針對 QA blocked 的 compact market line 與指定測試檔 expectations 收斂；未新增策略分類、未調整買賣判斷、未重構報文架構。

  ## 契約影響

  - 使用者可見 Telegram compact market line 在可買數 > 0 時新增 可買N 拆分。
  - 無可買時仍維持不可推薦語氣，不新增像推薦的新倉文案。
  - message list 入口與版本字串維持既有 v20.4.31，未改 DB payload 或 public strategy return shape。

  ## 直接消費者同步

  - 同步 tests/test_generator_report.py 對 Telegram rendered summary、未持倉卡、盤中/盤後簡報 expectations。
  - presentation/report.py 的 brief/evidence rendering path 已同步 compact line 行為。

  ## 未影響模組

  - 未改策略 decision / RR raw 計算公式。
  - 未改 DB schema、RLS、grant、policy、role、index、constraint。
  - 未執行 production write/backfill/live Telegram。
  - 未 commit/push。

  ## 已跑自檢命令

  - arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py --tb=short
  - 結果：146 passed, 225 warnings in 1.91s
  - warnings 皆為既有 dependency deprecation warnings。

  ## 殘留風險

  - 僅跑指定局部測試檔，未跑 full pytest。
  - 本輪為 Tech 自檢通過，不宣告 QA 通過。

  ## 旁支待辦

  - 若後續 Owner 要盤後 compact line 改名避免 交易執行 字樣，可另開任務；本輪依 QA blocker 僅補可買拆分與測試同步。
