# CHANGELOG:

  ## 修改內容

  - 任務尺寸與風險：risk_patch。本輪只修 QA blocker：cross-day context 的 source_of_truth 若混入 local_position_events / runtime / today/local 類非持久來源，generator 不得視為 ready。
  - core/generator.py 將 cross_day_ready() 改為必須 source_status == ready、source_of_truth 非空，且所有來源都屬於持久 DB 白名單；不再用 any() 允許 mixed source 通過。
  - 補 mixed-source negative：source_of_truth=["position_events", "local_position_events"] 即使 source_status=ready，也不觸發排序、prepare promotion、summary 追蹤最強或 detail 歷史文字。
  - 保留使用者可見版本 v20.4.1，並同步相關 header 測試期望。

  ## 修改檔案

  - core/generator.py
  - services/cross_day_context.py
  - tests/test_cross_day_context.py
  - tests/test_generator_report.py
  - tests/test_market_theme_evidence.py

  ## 最小改動策略

  - 沿用既有候選 diff，只在 generator source boundary 判斷補嚴格白名單。
  - 沒有重構 formatter、策略門檻、DB mapping 或報文分組。
  - 測試只補 blocker 指定的 mixed-source negative 與必要版本同步。

  ## 契約影響

  - cross_day_ready() 語意收緊：source_of_truth 只要包含非持久來源，就 fail closed。
  - sorting / summary / detail / prepare / dedupe 只能使用全部來源皆為持久 DB 白名單的 cross-day context。
  - 報文 header 維持 v20.4.1。
  - 未新增 schema、field、table、payload 欄位或 DB write path。

  ## 直接消費者同步

  - core/generator.py 內部直接消費者已同步走 cross_day_ready()：sort adjustment、repair label、detail line、prepare promotion、duplicate action、tracking summary。
  - tests/test_generator_report.py 已覆蓋 mixed persistent + local source 不得影響 sort/prepare/summary/detail。
  - tests/test_market_theme_evidence.py 已同步 v20.4.1 header 期望。

  ## 未影響模組

  - 未改 DB schema / migration。
  - 未改 Supabase write path。
  - 未改 replay / backfill。
  - 未改 watchlist。
  - 未執行 live Telegram。
  - 未執行 live Supabase write。
  - 未改 BUY / SELL / RR / 停損停利 / 過熱門檻。

  ## 已跑自檢命令

  - TMPDIR=.qa_tmp PYTHONPATH=.qa_tmp:. arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py：69 passed, 13 warnings。
  - TMPDIR=.qa_tmp PYTHONPATH=.qa_tmp:. arch -arm64 .venv/bin/python -m pytest tests/test_cross_day_context.py tests/test_generator_report.py tests/test_market_theme_evidence.py tests/test_notifier.py：92 passed, 13
    warnings。
  - git diff --check：通過，無輸出。

  ## 殘留風險

  - 未跑 full pytest。
  - 未做 production DB 真實讀取。
  - 未做 replay/backfill dry-run。
  - 未做 live Telegram / live Supabase 驗證。
  - source_of_truth 白名單目前由 generator 內常量判斷；若未來新增 Owner-approved persistent source，需要同步加入白名單。

  ## 旁支待辦

  - Phase 2 source precedence、schema mapping、production DB 欄位擴充與 backfill 仍不屬本輪。
  - 若後續要把 same-run guard 顯示給 Owner，需要另開 PM 任務定義手機報文契約。
