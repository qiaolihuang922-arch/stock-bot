# CHANGELOG: v20.4.42 未持倉非可買卡片 attribution 兩層可讀化

  ## 任務尺寸與風險

  normal_patch，QA L2。

  本輪改使用者可見未持倉非可買卡片 attribution、版本字串與 official replay assertions；不改策略方向、RR 公式、can_buy / is_valid_entry 判定、持倉狀態機、DB read/write 或 live Telegram。

  ## 修改內容

  - core/generator.py
      - VERSION 由 v20.4.41 升為 v20.4.42。
      - dominant_reject_reasons() 將 source unavailable 的主因由 source missing 改為人話化 資料來源缺失。
  - presentation/report.py
      - 非可買未持倉卡片 attribution 由單行 到達可買差距：... 改為固定兩行：
          - 卡關主因：...
          - 量化差距：...
      - 覆蓋 RR 不足差值、距突破 >4% 差值、過熱、盤後待確認、FAILED_BREAKOUT、source missing、strategy sample、limit lock、weak rebound。
      - source visible text 人話化，不再在相關卡片顯示 source missing / missing-source raw wording。
      - 真正可買卡片與 trend_continuation 小倉 BUY 卡片不輸出兩層卡關 attribution。
  - tests/test_generator_report.py
      - 更新 official message-list replay assertions，改驗 卡關主因 / 量化差距 兩行與 raw enum 不外露。
      - 更新 source missing / strategy sample 等人話化斷言。
      - 將所有 current-version expectation 由 v20.4.41 同步為 v20.4.42。
      - replay test 名稱同步為 test_v20_4_42_postmarket_unheld_gate_attribution_readability_message_list_replay。

  ## 修改檔案

  - core/generator.py
  - presentation/report.py
  - tests/test_generator_report.py

  ## 最小改動策略

  只修改 TASK 指定的 formatter / visible attribution / version / replay assertions。未順手重構，未清理旁支，未調整 fixture payload 以外的策略輸入語意，未擴大到 runner、DB、持倉或 live delivery。

  ## 契約影響

  - 使用者可見報文版本升為 v20.4.42。
  - 非可買未持倉卡片 attribution 契約改為兩行，順序固定為：
      - 卡關主因：{human_readable_primary_blocker}
      - 量化差距：{human_readable_gap_or_next_confirmation}
  - message list 內容有使用者可見文案變更，但未改 message list 順序、報文分組、payload shape、函式回傳結構、DB 寫入或 public helper contract。
  - 未改 RR / distance / heat / source eligibility 的計算與判定，只改呈現與測試期待。

  ## 直接消費者同步

  - Owner 手機閱讀 Telegram 盤後報文：非可買未持倉卡片可直接看到主因與量化差距。
  - official formatTelegramMessages / message-list replay：assertions 已同步到 v20.4.42 與兩層 attribution。
  - QA replay artifact / message-list snapshot：已覆蓋 RR 不足、距突破太遠、距突破 <=4% 負例、過熱、盤後待確認、突破失敗、source missing、strategy sample、limit lock、weak rebound、真正可買與 trend_continuation 小倉
    BUY。

  ## 未影響模組

  - 未改策略 decision。
  - 未改 RR 公式。
  - 未改 can_buy / is_valid_entry。
  - 未改持倉建議、持倉狀態機、買賣 / 加減碼 / 停損停利邏輯。
  - 未改 DB schema、DB read/write、production source-of-truth。
  - 未執行 live Telegram、live Supabase write、正式 backfill。
  - 未 commit / push。

  ## 已跑自檢命令

  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/v20_4_41_pytest_pycache_main2 arch -arm64 ./.venv/bin/python -m pytest tests/test_generator_report.py -k
    'v20_4_41_postmarket_unheld_gate_attribution_readability_message_list_replay or confirmed_evidence_preserves_limit_lock_chase_hard_blocker or v20_4_39_post_market_mixed_trend_and_prepare_keeps_trend_actionable or
    v20_0_14_post_market_fixture_uses_next_day_plan_semantics' -q -> 4 passed。
  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/v20_4_42_resync_pycache arch -arm64 ./.venv/bin/python -m pytest tests/test_generator_report.py -k
    'test_v20_4_42_postmarket_unheld_gate_attribution_readability_message_list_replay' -q -> 1 passed。
  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/v20_4_42_resync_pycache arch -arm64 ./.venv/bin/python -m pytest tests/test_generator_report.py -k 'test_0604_v20_4_37_generate_mobile_consistency_message_list_replay' -q
    -> 1 passed。
  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/v20_4_42_resync_pycache arch -arm64 ./.venv/bin/python -m py_compile core/generator.py presentation/report.py tests/test_generator_report.py -> passed。
  - git diff --check -> passed。
  - if rg 'v20\.4\.41' tests/test_generator_report.py; then exit 1; else echo "no v20.4.41 remains in tests/test_generator_report.py"; fi -> passed。

  ## 覆蓋層級

  - 已測：formatter、official generator / formatTelegramMessages message-list replay、report header / current version assertions。
  - 功能面 targeted replay 與先前 QA blocker 反證已通過。
  - 未測：full pytest、production runner artifact、read-only production source artifact、DB read/write、live Telegram。

  ## 殘留風險

  - 未跑 full pytest，風險限於本輪 normal_patch focused coverage。
  - 未取得真實 production runner artifact；目前只以等價 official message-list replay 驗收。
  - 若未來新增 source blocked 但仍保留有效 distance 的新路徑，需補 focused replay，避免重新外露不該顯示的距突破差距。
  - 本 CHANGELOG 不宣告 QA 通過；Tech 自檢只代表交付前檢查。

  ## 旁支待辦

  無。
