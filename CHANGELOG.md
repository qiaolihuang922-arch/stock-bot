# CHANGELOG:

  ## 任務尺寸與風險

  - 任務尺寸：tiny_patch
  - 風險判斷：只改 Telegram 第三則 short/evidence 文案與版本字串；不改策略 decision、DB read/write、payload shape、message list 結構或 live delivery。

  ## 修改內容

  - 將 core/generator.py 的 VERSION 升級為 v20.4.13。
  - 將第三則原 Evidence Compact raw/debug 類證據段落改為自然語言「簡短證據摘要」：
      - 持倉判斷依據用自然語言描述持久化紀錄是否可驗證。
      - 未持倉判斷依據用自然語言描述策略樣本 / 候選來源是否足夠。
      - 資料不足時明確 fail-closed，不把缺證據項目升格成行動建議。
  - 移除第三則漏斗中的 Source：漏斗 count ... do not show fake ... debug 類文字。
  - 移除已不再使用的舊 compact evidence raw formatter helper，避免 raw position_events/as_of 文案入口殘留。
  - 補測完整三則 Telegram output 順序、第三則禁止 debug terms、2356 第二段停利記憶不足自然語言 fail-closed、策略樣本 unavailable/insufficient fail-closed。
  - 同步既有版本斷言到 v20.4.13。

  ## 修改檔案

  - core/generator.py
  - tests/test_generator_report.py
  - tests/test_market_theme_evidence.py

  ## 最小改動策略

  - 保留 formatTelegramMessages() 回傳 list 結構：持倉 first、未持倉 second、short/evidence last；include_detail=True 時 Details Backup 仍追加最後。
  - 保留既有 formatter 入口名稱，避免改 runner / notifier 呼叫契約。
  - 只替換第三則 evidence 文案與必要測試，不重構報文系統。

  ## 契約影響

  - 使用者可見版本：v20.4.12 -> v20.4.13。
  - Telegram message order：不變。
  - Payload shape / function return shape：不變。
  - DB 寫入 / schema / RLS / grant / policy / role：不變。
  - 策略 decision / action mapping：不變。
  - 第三則使用者可見文案不再輸出 Evidence Compact raw heading、position_events、db_table、source_of_truth、latest_trade_date、lookback_range、raw Report：as_of、raw 候選：price/source 或漏斗 source debug 行。

  ## 直接消費者同步

  - Owner 手機 Telegram：第三則改為自然語言證據摘要，降低 debug 噪音。
  - QA sample 驗收：新增完整三則 output 與 unavailable strategy sample fixture。
  - Telegram runner / notifier：仍消費同一 message list；未修改 services/notifier.py。

  ## 未影響模組

  - 策略買賣 / 加減碼 / 停損停利判斷未改。
  - DB schema、production write、backfill、live Telegram 未碰。
  - 第一則持倉卡與第二則未持倉卡主結構、排序與策略語意未改。
  - market/theme evidence 讀取邏輯未改，只同步版本測試期望。

  ## 已跑自檢命令

  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m py_compile core/generator.py services/notifier.py：passed
  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py tests/test_market_theme_evidence.py tests/test_notifier.py：119 passed，169
    warnings（第三方 deprecation 類）
  - git diff --check：passed
  - 追加 sample probe：完整三則 / detail output 順序與第三則禁止 debug terms 檢查 passed

  ## 殘留風險

  - 本輪未重設整份第三則 summary 結構，只針對 TASK 指定的 evidence/debug 噪音與漏斗 source debug 行降噪。
  - 未做 live Telegram delivery；Tech 自檢只代表交付前檢查，不代表 QA 通過。

  ## 旁支待辦

  - 若 Owner 後續要求第三則整體更短，可另開任務收斂 summary 主體。
  - Telegram reply markup 仍附在最後一則 message 的 delivery consumer 風險未納入本輪。
