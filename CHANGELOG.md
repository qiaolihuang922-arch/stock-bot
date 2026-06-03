# CHANGELOG: evidence_score_effective_market_freshness_v20_4_34

  ## 任務尺寸與風險

  risk_patch。原因：改到 evidence score / modifier helper、Telegram/official generator 證據分數效果，以及 GitHub Actions daily_evidence runner fail-closed 行為；未改 RR 公式、DB schema、持倉狀態機或 live delivery。

  ## 修改內容

  - compute_evidence_score() 的 per-stock strategy 分量現在可直接消費各股 backtest_context：有 sample 但沒有 source_status 時，不再被全局 strategy manifest 的 partial / insufficient 拉成 unavailable。
  - backtest_context.reference / reference_level 支援 高 / high / reliable / strong 作為 sample >= 10 的 ready 判斷依據。
  - avg_return 轉為 numeric 後判斷，避免字串型 backtest 欄位造成比較風險。
  - Phase 3 daily evidence workflow cron 從 25 5 * * 1-5 改為 0 6 * * 1-5，對應台北收盤後。
  - scripts/run_phase3_evidence_automation.py 新增 --require-market-theme-payload：daily evidence runner 缺 MARKET_THEME_APPROVED_PAYLOAD 時 fail closed，回傳非 0。
  - market/theme approved payload 寫入前驗證 payload rows 的 trade_date 必須等於本次 trading_day；不符時不進 write CLI。
  - 補測緯創 sample 36、華邦 sample 38、低樣本、無 backtest、弱勢/失敗不抬分、workflow secret 缺失 fail-closed、payload trade_date mismatch。

  ## 修改檔案

  - .github/workflows/stock-bot.yml
  - core/generator.py
  - scripts/run_phase3_evidence_automation.py
  - tests/test_generator_report.py
  - tests/test_phase3_evidence_automation.py
  - tests/test_workflow_runtime_config.py

  ## 最小改動策略

  只修改 TASK 指定的 evidence source / daily evidence runner / 相關測試。既有 RR 顯示、防抖、報文版本、排序公式、DB write CLI、Telegram delivery 路徑未擴大重構。

  ## 契約影響

  - public helper _per_stock_strategy_sample_evidence_payload() 行為改變：per-stock backtest_context.sample 成為 strategy evidence source，可在全局 sample partial 時仍判定該股 ready。
  - compute_evidence_score() / apply_evidence_confidence() 的輸出可因此讓合格股票 final_confidence != technical_confidence。
  - 弱勢 / FAIL / FAILED_BREAKOUT 等既有 guard 保持 modifier <= 1.0。
  - runner CLI 新增 --require-market-theme-payload，缺 approved payload 時非 0 exit。
  - 使用者可見版本維持 v20.4.34；掃描結果：core/generator.py:72 VERSION = "v20.4.34"。本輪是 v20.4.34 同版契約修復，不升版。

  ## 直接消費者同步

  - official message-list generator 測試新增緯創 / 華邦等價 replay，覆蓋卡片分數行與樣本行。
  - GitHub Actions daily_evidence step 已同步傳入 --require-market-theme-payload。
  - Phase 3 automation tests 已同步 secret 缺失與 payload date gate。
  - workflow runtime tests 已同步新 cron 與 runner command。

  ## 未影響模組

  - RR 公式未改。
  - DB schema / RLS / grant / policy / role / index / constraint 未改。
  - scripts/write_market_theme_confirmed_evidence.py approved write CLI 未改。
  - live Telegram delivery 未執行、未修改。
  - 持倉狀態機、同日買入風控、光寶科既有防抖邏輯未改。

  ## 已跑自檢命令

  - arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py：156 passed，241 warnings。
  - arch -arm64 .venv/bin/python -m pytest tests/test_phase3_evidence_automation.py tests/test_workflow_runtime_config.py：23 passed。
  - PYTHONPYCACHEPREFIX=/private/tmp/stock_bot_pycache arch -arm64 .venv/bin/python -m py_compile core/generator.py scripts/run_phase3_evidence_automation.py：passed。
  - git diff --check：passed。
  - rg -n '^VERSION = ' core/generator.py：VERSION = "v20.4.34"。
  - 備註：python 不在 PATH；直接用 .venv/bin/python 會遇到 pydantic_core 架構不相容，已改用 arch -arm64 .venv/bin/python 完成測試。

  ## 覆蓋層級

  helper：覆蓋 per-stock strategy evidence payload、modifier 生效、弱勢不抬分、runner payload gate。
  formatter / official generator：覆蓋 Telegram message-list 卡片分數、回測樣本、RR/防抖既有 replay。
  runner artifact：覆蓋 workflow command、missing secret fail-closed、payload trade_date mismatch。
  production source：未讀 production DB、未做 live write；market daily freshness 的真實 production row 仍需 QA/Architect safe read-only artifact 或正式 runner 證據驗。

  ## 殘留風險

  - 本輪未執行 production daily_evidence smoke，無法證明 market_theme_confirmed_evidence 已有 2026-06-03 真實行。
  - 若 GitHub secret MARKET_THEME_APPROVED_PAYLOAD 未配置，daily_evidence 會正確 fail closed，但不會完成 market/theme 當日保鮮。
  - 測試使用等價 fixture / replay，未接觸 live Supabase 或 live Telegram。

  ## 旁支待辦

  - QA 若要驗 market daily freshness 完成口徑，需要 safe read-only artifact 或正式 runner artifact，確認 production market_theme_confirmed_evidence.trade_date 當日存在且 report 背景為 confirmed_trend。
  - 若 Owner 要完全自動生成 approved payload 而不依賴 secret，需另開任務確認 approved service API 契約，不能在本輪改成繞過 approved payload gate。
