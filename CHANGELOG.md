# CHANGELOG:

  ## 任務尺寸與風險

  - 任務尺寸：normal_patch
  - 版本：v20.4.15
  - 風險：修改 Telegram 第三則 message 結構與 formatter/helper 輸出，屬 message list / public helper contract 變更；未改策略 decision、DB/write path、live Telegram。

  ## 修改內容

  - 將第三則 Telegram 改為 🧾 v20.4.15 簡報＋資料依據。
  - 第三則固定只有兩個主要入口：
      - 決策簡報
      - 資料依據
  - 決策簡報 保留既有 summary 消費者需要的內容：今日結論、交易執行、持倉風控檢查、未持倉漏斗、詳情索引等，並去除 raw source / legacy strategy evidence noise。
  - 資料依據 集中呈現：
      - market/theme production 狀態
      - strategy sample source status 與 fail-closed
      - 持倉/候選 source-of-truth 狀態與限制
  - 修正 position_warning / source-missing early return：不再只回單一 summary，改為三則 Telegram message，維持持倉、未持倉、第三則順序。
  - 使用者可見版本升至 v20.4.15。

  ## 修改檔案

  - core/generator.py
  - tests/test_generator_report.py
  - tests/test_market_theme_evidence.py

  ## 最小改動策略

  - 只改第三則 Telegram 組裝、source-missing early return 與對應測試。
  - 不碰第一則持倉卡片、第二則未持倉卡片。
  - 不改策略判斷、持倉狀態機、DB schema/write path、live delivery。

  ## 契約影響

  - formatTelegramMessages() 仍維持：
      - messages[0] 持倉
      - messages[1] 未持倉/候選
      - messages[2] 第三則 簡報＋資料依據
      - include_detail=True 時 Details Backup 仍追加最後
  - 第三則不再使用 v20.4.14 簡短證據摘要 標題。
  - format_evidence_compact_message() 仍保留 helper 入口，但輸出改為 v20.4.15 的 簡報＋資料依據 結構。
  - source-missing / position warning 路徑也產出三則訊息，避免 summary_message() / evidence_message() 類直接消費者找不到第三則。

  ## 直接消費者同步

  - Telegram notifier/message list consumer：三則順序維持，reply markup 仍可附著最後主訊息。
  - 測試 helper summary_message() / evidence_message()：同步定位 簡報＋資料依據。
  - dry-run / sample 驗證：第三則保留 summary 決策摘要內容，同時集中資料依據。

  ## 未影響模組

  - 未改策略 decision / BUY SELL / 加減碼 / 停利停損判斷。
  - 未改 DB schema、RLS、grant、policy、role、index、constraint。
  - 未新增 write path、backfill、production DML。
  - 未執行 live Telegram。
  - 未改第一、第二則卡片分類、排序、行動文案。

  ## 已跑自檢命令

  - git diff --check：passed
  - arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py tests/test_market_theme_evidence.py tests/test_notifier.py：119 passed, 169 warnings
  - 補充環境狀態：直接跑 pytest 時 shell PATH 無 pytest；直接 .venv/bin/python 為 x86_64/arm64 架構不一致，改用 arch -arm64 .venv/bin/python 後測試通過。

  ## 殘留風險

  - 未跑 full pytest，僅依 Architect 指令跑 L2 scoped tests。
  - 未做 production DB read/write、replay/backfill、live Telegram。
  - 第三則目前保留完整 summary 決策段落於 決策簡報，若 Owner 後續要求更短手機版，需要另開文案壓縮任務。

  ## 旁支待辦

  - 2356 ledger/source-of-truth 稽核。
  - reply markup 附著最後一則 message 的 delivery consumer 風險。
  - 全報文文案盤點。
  - strategy evidence 模型重構。
  - production data backfill 或 DB schema 設計。
