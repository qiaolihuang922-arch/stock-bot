# CHANGELOG:

  ## 任務尺寸與風險

  normal_patch。Telegram 使用者可見卡片 wording / message-list 顯示語意修正；未改策略 decision、RR 公式、DB/write、持倉狀態機或 live Telegram。

  ## 修改內容

  - VERSION 升至 v20.4.44。
  - 未持倉卡片補齊人話交易語意：卡關主因、量化差距、解鎖、依據。
  - 移除可見卡片中的 generic 決策證據：來源可追溯。
  - raw/internal gate 顯示改成人話，例如 overheat、failed breakout、holding hard risk。
  - 盤後 prepare 卡改為明確 買點：明日準備｜不可下單，解鎖為開盤後守突破區 / 不追價。
  - 持倉 hard stop 卡顯示跌破停損線距離，不再外露 hard stop / 持倉風控。

  ## 修改檔案

  - core/generator.py
  - presentation/report.py
  - tests/test_generator_report.py

  ## 最小改動策略

  只改 Telegram formatter wording、VERSION、official message-list focused tests。保留 v20.4.43 decision_judgment payload 與 hard-gate fail-closed 判斷，不碰策略閾值、RR 計算、DB/write/live delivery。

  ## 契約影響

  - 使用者可見報文 header/version 改為 v20.4.44。
  - Telegram card message list wording 改變。
  - 未改函式回傳結構、payload shape、DB contract、策略 decision、message 分組順序。
  - decision_judgment 內部 blocking/progress reasons 保留，僅 formatter 轉成人話或隱藏 generic 可追溯 wording。

  ## 直接消費者同步

  - formatTelegramMessages official message-list tests 已同步。
  - Owner specimen 等價 replay 覆蓋 prepare、overheat/failed breakout blocker priority、holding hard stop、source missing/error/conflict fail-closed。
  - QA 可沿同一 official message-list replay 驗收。

  ## 未影響模組

  - strategy decision / can_buy / is_valid_entry
  - RR formula / heat / breakout 判定
  - DB schema / RLS / grant / policy / write path
  - live Telegram delivery
  - replay/backfill
  - holding state machine

  ## 已跑自檢命令

  - pytest tests/test_generator_report.py -k 'v20_4_42_postmarket_unheld_gate_attribution_readability_message_list_replay or v20_4_43_evidence_chain_decision_judgments_cover_eligibility_layers or
    v20_4_43_evidence_chain_missing_error_conflict_fail_closed or v20_4_43_holding_hard_stop_judgment_is_visible_and_non_bypass' -q -> 4 passed
  - pytest tests/test_generator_report.py -k 'v20_4_43 or v20_4_42_postmarket_unheld_gate_attribution_readability_message_list_replay or confirmed_evidence_preserves_limit_lock_chase_hard_blocker or
    v20_4_39_post_market_mixed_trend_and_prepare_keeps_trend_actionable or v20_0_14_post_market_fixture_uses_next_day_plan_semantics or v20_4_18_structural_artifacts_cover_three_fail_closed_cases or
    v20_4_20_maturity_report or v20_4_25_strategy_sample_source_error_blocks_action_without_hiding_available_price or v20_4_16_unheld_card_fails_closed_when_ohlcv_missing or
    trend_continuation_official_report_has_separate_small_buy_bucket' -q -> 14 passed
  - pytest tests/test_generator_report.py -k 'eight_day_confirmed_market_theme_is_decision_eligible' -q -> 1 passed
  - py_compile core/generator.py presentation/report.py tests/test_generator_report.py -> passed
  - git diff --check -> passed

  ## 殘留風險

  未跑 full pytest、production runner artifact、production DB source artifact、DB read/write、live Telegram。Tech 自檢不代表 QA 通過。

  ## 旁支待辦

  - 全量文案 redesign 不在本輪。
  - production source artifact / live Telegram 需另走授權流程。
  - 若未來要更細分 prepare/buy evidence line 排序，可另開報文 wording 任務。
