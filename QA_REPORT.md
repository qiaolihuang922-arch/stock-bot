# QA_REPORT:

  ## 測試範圍

  本輪 QA 依 TASK major / L3 與 Architect Re-QA 指令，聚焦 Phase 3 scheduled evidence automation，不擴大到 Phase 1/2/2b score、RR、策略 decision、正式 backfill 或 live Telegram。

  檢查文件與 diff：

  - TASK.md
  - CHANGELOG.md
  - .github/workflows/stock-bot.yml
  - scripts/run_phase3_evidence_automation.py
  - core/generator.py
  - services/daily_snapshot_store.py
  - 相關測試檔

  可吸收 diff：

  - workflow daily_evidence schedule/runtime config/bot skip
  - Phase 3 runner
  - daily snapshot read-after-write helper
  - generator optional write_results 回傳
  - 對應 tests

  worktree 殘留：

  - 未見與本輪無關的 product/test 殘留；git status --short 只列本輪相關檔案與 CHANGELOG.md。

  ## 風險預算與停止條件

  本輪最值得抓的風險：

  1. scheduled daily_evidence 誤送 Telegram 或進 live bot。
     驗證：workflow RUN_MODE schedule 預設、runtime config 不要求 Telegram、Run bot step skip。
     停止條件：scheduled path 仍可能跑 main.py 或要求 Telegram secrets。
  2. 非交易日 / 13:20 前 / unknown calendar 誤寫 production evidence。
     驗證：runner gate、TWSE confirmed trading day check、skip log、額外 13:19 direct write negative probe。
     停止條件：任何 skip case 仍呼叫 daily snapshot 或 market/theme write。
  3. guard / read-after-write failure 被吞錯或 stale holiday/unknown 被累積。
     驗證：approved CLI subprocess return code propagation、read-after-write failure path、額外 unknown calendar stale probe。
     停止條件：failure 回 0、印 confirmed、或 unknown/holiday 累積 stale alert。

  ## 關聯風險掃描

  通過項：

  - scheduled cron 為 25 5 * * 1-5，換算 Asia/Taipei 為 13:25，符合 13:20+。
  - schedule 預設 RUN_MODE=daily_evidence；Run bot step 對 daily_evidence 直接 skip，不送 Telegram。
  - daily_evidence runtime config 允許 TOKEN="" / CHAT_ID=""，不要求 Telegram secrets。
  - runner 在 weekend、13:20 前、TWSE source missing/source-error/holiday/unknown 時 skip，且 log 兩個 source 的 EVIDENCE_WRITE_SKIPPED。
  - market/theme 寫入仍呼叫 scripts/write_market_theme_confirmed_evidence.py --execute，沒有新增直接 DML path。
  - approved CLI 既有 guard/read-after-write failure 仍回 nonzero；Phase 3 wrapper 對 subprocess nonzero 轉 EVIDENCE_WRITE_FAILED ... action=fail_closed 並回傳非 0。
  - daily snapshot read-after-write helper 會檢查 expected watchlist rows，缺 row 時 fail。

  ## 跨區塊語意一致性

  TASK / CHANGELOG / diff 大致一致：

  - TASK 要 scheduled runner、confirmed trading day + 13:20 後、非交易日 skip、approved market/theme write path、read-after-write、guard failure fail closed。
  - CHANGELOG 宣稱的 TWSE confirmed trading day gate、stale confirmed-day 計數、daily_evidence 不送 Telegram、approved CLI path，均可在 diff 找到對應實作或測試。
  - 未見 DB schema / RLS / grant / policy / role / index / constraint 變更。
  - 未見 evidence_score / final_confidence / decision_eligible / funnel modifier / RR / 策略 decision 變更。

  注意：TASK 原始尺寸是 major/L3，CHANGELOG 將 Re-Tech 描述為修 blocked 缺口的 risk_patch。本次 QA 仍按 L3 風險檢查 workflow、guard、consumer 與負面案例，未因此降級驗收。

  ## 使用者誤讀風險

  - scheduled daily_evidence 不會產生 Telegram 報文，因此手機閱讀風險主要落在 workflow log。
  - stale alert log 形狀為 EVIDENCE_STALE_ALERT source=... consecutive_days=... status=... action=fail_closed，不含可買、推薦、準備買入語氣。
  - skip / failed / confirmed log 都是單行 grepable，能區分 skip、fail closed、read-after-write ok，不會把 guard failure 誤讀成 confirmed。
  - backfill_and_bot 仍會跑 Phase 3 automation 並跑 bot；這是 manual run mode，不是 scheduled daily_evidence。本輪不建議整包擴成 live-delivery 變更。

  ## 質疑與反證

  Tech 自檢外，QA 補充反證：

  - unknown calendar stale probe：
    build_stale_alerts(..., trading_day_checker=source-error) 回 alerts=[]，確認 unknown weekday 不累積 stale。
  - 13:19 direct consumer negative probe：
    monkeypatch 兩個 write entry 為一呼叫即失敗，執行 main --now 2026-06-02T13:19:00+08:00 回 0 並只輸出兩條 skip log，確認 before-close 不進 write path。
  - 初次 .venv/bin/python pytest 因 x86_64 Python 載入 arm64 pydantic_core 失敗；已依 CHANGELOG 用 arch -arm64 .venv/bin/python 重跑，不以環境問題跳過。

  測試結果：

  - arch -arm64 .venv/bin/python -m pytest -q tests/test_phase3_evidence_automation.py tests/test_daily_snapshot_store.py tests/test_workflow_runtime_config.py
      - 29 passed, 13 warnings
  - arch -arm64 .venv/bin/python -m py_compile ...
      - passed
  - git diff --check
      - passed

  ## 未測項目

  - 未執行 live Telegram。
  - 未執行 production write。
  - 未做正式 historical bulk backfill。
  - 未跑 full repo pytest；本輪 L3 驗證已覆蓋 workflow / runner / guard / read-after-write / stale 負面路徑，未擴大到策略全矩陣。
  - 未驗 production TWSE / Supabase 現場可用性；本輪以 fixture / monkeypatch / approved CLI contract 驗證 fail-closed 行為。

  ## QA 結論

  通過
