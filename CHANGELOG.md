# CHANGELOG:

  ## 任務尺寸與風險

  - 任務尺寸：normal_patch
  - 風險判斷：修改 Telegram 市場 / 題材 evidence 顯示與 fallback contract，涉及使用者可見報文與直接 formatter 消費者；未改交易策略、DB schema、watchlist universe、live path。

  ## 修改內容

  - 將 Telegram 使用者可見版本升為 v20.3.0。
  - 在缺 DB evidence table/cache 時，允許用本次 runtime results_map 生成 watchlist_breadth fallback evidence。
  - runtime fallback source 標記為 runtime_fallback=True，不計入 confirmed gate，避免缺 market_index / sector_index 時被確認為 confirmed。
  - 新增 missing_source_reasons、runtime_fallback、runtime_supportive evidence 回傳欄位，用於 Telegram 文案區分缺 DB/cache、缺 runtime breadth、缺 market_index、缺 sector_index。
  - Telegram 市場 / 題材 evidence 區塊新增：
      - 市場證據：weak/runtime
      - 題材證據：weak/runtime
      - absent/missing-source 缺來源說明
  - runtime supportive 但缺 index 時，文案明確標示「內部觀察池偏強 / 偏支持，但缺大盤 / 族群指數，未確認」。
  - runtime data 不足時，文案列出缺來源，不再只輸出模糊 absent。
  - 補測 runtime fallback weak、missing-source absent、formatter 長報文、版本 header、策略 smoke。

  ## 修改檔案

  - core/generator.py
  - core/market_theme_evidence.py
  - tests/test_market_theme_evidence.py
  - tests/test_generator_report.py
  - tests/test_notifier.py

  ## 最小改動策略

  - 只改 market/theme evidence helper、Telegram summary formatter 入口、版本常量與直接測試。
  - 未重構 evidence 架構。
  - 未新增 DB / migration / Supabase write / backfill / live Telegram。
  - 未改 BUY/SELL/RR/過熱/漲停不追/可準備分類邏輯。

  ## 契約影響

  - build_market_theme_evidence() 新增 optional missing_db_evidence=False 參數。
  - evidence dict 新增欄位：runtime_fallback、runtime_supportive、missing_source_reasons。
  - runtime fallback evidence 最高只形成 weak/runtime 或 absent/missing-source；不會輸出 confirmed。
  - Telegram 市場 / 題材 evidence message list 在 runtime fallback 或 missing-source 情境會輸出新的手機優先文案。
  - 版本 header 從 v20.2.5 升為 v20.3.0。

  ## 直接消費者同步

  - core/generator.py 的 market_theme_summary_evidence() 已同步 dict evidence 與非 dict market_summary 路徑。
  - format_market_theme_summary_lines() 已同步 weak/runtime 與 absent/missing-source 文案。
  - tests/test_market_theme_evidence.py 已覆蓋 provider contract 與 formatter summary contract。
  - tests/test_generator_report.py 已同步接近真實 Telegram 長報文 fixture 與版本期望。
  - tests/test_notifier.py 已同步 header 版本直接消費者。

  ## 未影響模組

  - 未修改策略 decision engine。
  - 未修改 DB schema / migration。
  - 未修改 Supabase write path。
  - 未修改 watchlist universe 或 watchlist source。
  - 未修改 replay / backfill。
  - 未執行 live Telegram delivery。
  - 未執行 live Supabase write。
  - 未新增交易、加碼、可買或可準備建議。

  ## 已跑自檢命令

  - python -m pytest tests/test_market_theme_evidence.py tests/test_generator_report.py -q
      - 結果：失敗，系統 python 不存在。
  - .venv/bin/python -m pytest tests/test_market_theme_evidence.py tests/test_generator_report.py -q
      - 結果：失敗，.venv 內 pydantic_core 為 arm64，但預設 Python 進程需要 x86_64。
  - arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence.py tests/test_generator_report.py tests/test_notifier.py tests/test_signal_validator.py tests/test_analysis_engine.py -q
      - 結果：120 passed, 21 warnings
  - git diff --check
      - 結果：通過
  - git diff -- supabase scripts services core/watchlist.py config.py requirements.txt
      - 結果：無 diff

  ## 殘留風險

  - 本輪 runtime fallback 只使用既有 results_map 觀察池廣度，不代表正式 market_index / sector_index evidence。
  - 缺 DB/cache 的判斷由 formatter/provider 入口推導，尚未接正式 evidence table/cache 存在性檢查。
  - warnings 來自既有依賴與 Supabase/Pydantic deprecation，非本輪新增。

  ## 旁支待辦

  - 正式 evidence table / migration。
  - Supabase evidence write。
  - evidence backfill。
  - market_index / sector_index 外部資料接入。
  - 長期 market/theme evidence scoring 改版。
  - watchlist breadth 指標重設。
