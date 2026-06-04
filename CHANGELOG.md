# CHANGELOG: v20.4.40 Telegram 未持倉 gate attribution 試行

  ## 任務尺寸與風險

  normal_patch；只改 Telegram 未持倉卡片 formatter 的可讀 attribution 與 official message-list replay 測試，不改策略判斷、RR、can_buy/is_valid_entry、DB 或 live delivery。

  ## 修改內容

  - 使用者可見版本同步為 v20.4.40。
  - 未持倉非可買卡片新增 到達可買差距 行，最多顯示 1-3 個可由現有 payload/formatter input 穩定取得的 gate。
  - 可買卡與 trend_continuation 小倉 BUY 卡不顯示差距行。
  - 修正返工阻塞點：LIMIT_LOCK / LIMIT_REBOUND / 不可追高優先輸出開板回測 gate；trade_state=AVOID/EXTENDED 但 heat_state=NORMAL 不再輸出 heat NORMAL/需降溫，只有 HOT/EXTREME 或 blocker 明確過熱才輸出 heat gate。

  ## 修改檔案

  - core/generator.py
  - presentation/report.py
  - tests/test_generator_report.py

  ## 最小改動策略

  - 只新增未持倉卡片內部 helper 與插入一行 attribution。
  - 測試只補 official formatTelegramMessages / message-list replay 場景與版本同步斷言。
  - 沒有重構 formatter、沒有改候選排序、沒有改策略輸出或資料來源。

  ## 契約影響

  - Telegram 未持倉非可買卡片新增單行輸出：到達可買差距：...。
  - 報文版本 header/summary 常量同步為 v20.4.40。
  - 未改函式回傳結構、payload shape、message list 分組順序、DB contract、strategy decision、RR、can_buy/is_valid_entry。

  ## 直接消費者同步

  - formatTelegramUnheldCard 直接消費 _unheld_buy_gap_line。
  - official formatTelegramMessages replay 已同步驗證 RR不足、過熱、source missing、可買、trend_continuation、LIMIT_LOCK/AVOID+NORMAL 負面案例。
  - 測試同步確認不可買卡片不出現推薦式 建議買入 / 可立即買 語氣。

  ## 未影響模組

  - strategy decision / position decision
  - RR 計算
  - can_buy / is_valid_entry contract
  - DB schema / RLS / grant / policy / role / write path
  - live Telegram delivery
  - replay/backfill

  ## 已跑自檢命令

  - arch -arm64 ./.venv/bin/python -m pytest tests/test_generator_report.py -k 'v20_4_40_unheld_non_buy_cards_show_gate_attribution_only or confirmed_evidence_preserves_limit_lock_chase_hard_blocker or
    v20_4_39_post_market_mixed_trend_and_prepare_keeps_trend_actionable or v20_0_14_post_market_fixture_uses_next_day_plan_semantics' -q -> 4 passed
  - PYTHONPYCACHEPREFIX=/private/tmp/v20_4_40_pycache arch -arm64 ./.venv/bin/python -m py_compile core/generator.py presentation/report.py tests/test_generator_report.py -> passed
  - git diff --check -> passed

  ## 覆蓋層級

  - formatter/helper：_unheld_buy_gap_line 的 visible output 由 official card replay 間接覆蓋。
  - official generator/message-list：formatTelegramMessages replay 覆蓋 Summary 與未持倉卡片。
  - direct consumer：RR不足、過熱、source missing、可買、trend_continuation、LIMIT_LOCK/AVOID+NORMAL。
  - 未覆蓋：production runner artifact、live Telegram、DB read/write、full pytest。

  ## 殘留風險

  - 未跑 full pytest、production runner artifact、live Telegram、DB read/write。
  - gate 排序仍是 formatter 內可取得欄位的保守優先序，不是完整策略診斷排名。

  ## 旁支待辦

  - 若 Owner 後續要更精細的 gate ranking 或更多診斷欄位，需另開任務；本輪只交付未持倉 gate attribution 試行。
