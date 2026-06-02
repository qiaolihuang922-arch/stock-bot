# CHANGELOG:

  ## 任務尺寸與風險

  - 任務尺寸：risk_patch。
  - 風險判斷：TASK 原始任務為 Phase 3 production evidence automation，涉及 scheduled runner 與 approved production write path；本輪 Re-Tech 只修 QA blocked 的交易日確認與 stale 計數缺口，不改 DB schema、策略分數、報文決
    策或 live delivery。

  ## 修改內容

  - Phase 3 runner 不再把 weekday 當完整 trading day source-of-truth。
  - 13:20+ Asia/Taipei 盤後 gate 保留；週末仍 skip。
  - 平日盤後寫入前新增 TWSE official MI_INDEX historical rows 確認：
      - 確認成功才執行 daily_signal_snapshot 與 market_theme_confirmed_evidence。
      - TWSE source 空、source-error、holiday 或 unknown calendar 時 fail closed。
      - skip log 固定輸出 EVIDENCE_WRITE_SKIPPED ... reason=not-confirmed-trading-day。
  - stale/unavailable alert 改為只累積明確 confirmed trading day：
      - JSON probe entry 必須有 trading_day_confirmed: true，或測試注入 checker 確認。
      - weekday holiday / unknown calendar 不累積 stale trading-day alert。
  - 修正無 MARKET_THEME_APPROVED_PAYLOAD 時 runner payload 來源：
      - 改用既有 fetch_twse_historical_index_rows() / fetch_twse_historical_breadth_rows() readonly TWSE source。
      - 保持後續寫入仍走 scripts/write_market_theme_confirmed_evidence.py --execute approved write CLI。
  - 保留既有候選功能：
      - GitHub Actions scheduled daily_evidence mode。
      - daily evidence mode 不要求 Telegram secrets、不跑 live bot delivery。
      - generate_report(return_write_results=True) 提供 runner read-after-write 判斷所需 write results。
      - read_daily_signal_snapshot_status() 檢查 expected watchlist rows。

  ## 修改檔案

  - .github/workflows/stock-bot.yml
  - scripts/run_phase3_evidence_automation.py
  - core/generator.py
  - services/daily_snapshot_store.py
  - tests/test_phase3_evidence_automation.py
  - tests/test_daily_snapshot_store.py
  - tests/test_workflow_runtime_config.py
  - 未直接編輯 CHANGELOG.md；本內容供 runner 寫入。

  ## 最小改動策略

  - 只在 Phase 3 runner guard 層補交易日確認，不改既有 approved write script 的 guard。
  - 不新增交易日資料表、不新增 holiday calendar schema。
  - 使用 repo 既有 TWSE official market/theme readonly source 確認交易日；無法確認即 fail closed。
  - 測試用 fake TWSE rows / source-error，不打外部網路、不寫 production。

  ## 契約影響

  - CLI log 新增/保留：
      - EVIDENCE_WRITE_SKIPPED source=... trading_day=... reason=not-confirmed-trading-day
      - EVIDENCE_WRITE_CONFIRMED source=... trading_day=... read_after_write=ok
      - EVIDENCE_WRITE_FAILED source=... trading_day=... action=fail_closed
      - EVIDENCE_STALE_ALERT source=... consecutive_days=... status=... action=fail_closed
  - generate_report() 預設回傳不變；只有呼叫 return_write_results=True 時回傳第三個 write_results dict，供 Phase 3 runner 使用。
  - stale alert probe contract 收緊：未確認交易日不計入 consecutive trading days。
  - 不改 message list 順序、Telegram 報文分組、payload schema、DB schema、evidence_score、final_confidence、decision_eligible 或 funnel modifier。

  ## 直接消費者同步

  - GitHub Actions scheduled runner 已接 daily_evidence mode，且不進 live bot delivery。
  - Phase 3 runner 同步使用 generate_report(return_write_results=True) 與 read_daily_signal_snapshot_status()。
  - market/theme confirmed evidence 仍透過 scripts/write_market_theme_confirmed_evidence.py --execute，未繞過 6 層 guard 與 read-after-write。
  - tests 同步覆蓋 workflow command、runtime config、runner time/trading-day guard、approved CLI path、read-after-write failure、stale alert confirmed trading-day 計數。

  ## 未影響模組

  - 未改 DB schema / RLS / grant / policy / role / index / constraint。
  - 未改 production DML interface 以外的直接寫庫路徑。
  - 未改 evidence_score / final_confidence / decision_eligible / funnel evidence modifier。
  - 未改 RR 公式、策略核心、持倉建議、買賣 / 加減碼 / 停損停利 decision。
  - 未執行 live Telegram、正式 backfill 或 production write。

  ## 已跑自檢命令

  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_phase3_evidence_automation.py tests/test_daily_snapshot_store.py tests/
    test_workflow_runtime_config.py
      - 結果：29 passed，13 warnings。
  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m py_compile scripts/run_phase3_evidence_automation.py services/daily_snapshot_store.py core/generator.py tests/
    test_phase3_evidence_automation.py tests/test_daily_snapshot_store.py tests/test_workflow_runtime_config.py
      - 結果：passed。
  - git diff --check
      - 結果：passed。
  - 補充：直接 .venv/bin/python pytest 曾因主 repo arm64 wheel 與 x86_64 Python 架構不符失敗；已用既有 arm64 命令重跑通過。

  ## 殘留風險

  - 未新增正式 trading calendar DB/source；交易日確認依賴既有 TWSE official MI_INDEX readonly source。TWSE source 不可用時會 fail closed，不寫 snapshot / market-theme，不累積 stale alert。
  - GitHub cron 仍是週一到週五觸發；台股休市日會由 runner 的 TWSE confirmation gate skip，不作為交易日寫入。
  - 本輪未做 live production write 驗證；需 QA L3 依 TASK 用 sandbox/fixture 或 approved safe artifact 驗證 workflow 與 guard。

  ## 旁支待辦

  - 若 Owner 要降低 TWSE source outage 導致的 skip，可另開任務建立 approved trading calendar source-of-truth。
  - 後續 Phase 1/2/2b evidence_score / final_confidence / funnel modifier 接入仍未開始。
  - production historical bulk backfill、live Telegram delivery 不在本輪範圍。
