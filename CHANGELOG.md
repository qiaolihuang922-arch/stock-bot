# CHANGELOG: evidence-chain hard-gate fail-closed fix v20.4.43

  ## 任務尺寸與風險

  risk_patch。修正 v20.4.43 candidate 的真實 hard-gate bug：decision_judgment.blocking_reasons 不能只停在可見文字；RR不足、過熱/EXTREME、突破失敗、source-error/conflict、hard stop/holding risk 等硬閘門存在時，
  eligibility / summary / funnel / card 必須 fail closed。未改 DB/live/schema/write path，未 commit/push，未宣告 QA 通過。

  ## 修改內容

  - core/generator.py
      - 新增未持倉 hard-gate reason 聚合，統一判斷 RR不足、overheat/EXTREME、failed breakout、追高/漲停、量能、source-error/missing/conflict。
      - decision_judgment.eligibility_state 遇 hard blocker 時強制 blocked，不再保留 buy / trend_continuation / prepare。
      - unheld_funnel_state 遇 hard blocker 時同步降級到既有非買分組，例如 RR不足降到 等RR修復，過熱降到 等冷卻，量能降到 等量能，其他不可行動降到 淘汰。
  - presentation/report.py
      - 卡片狀態與 fail-closed funnel 對齊，避免低 RR trend continuation 仍顯示綠卡。
      - hard-gate 降級後保留 v20.4.42 的 卡關主因 / 量化差距 兩行，不再因 decision_type=trend_continuation 壓掉 gap line。
      - 補回 淘汰 標題顯示，避免 failed breakout 卡片回退成 generic 不買。
  - tests/test_generator_report.py
      - 新增 official formatTelegramMessages replay：trend_continuation_payload with rr/risk_reward = 0.8 必須 fail closed。
      - 反證 summary 不顯示 新倉建議 1、趨勢延續買入 1 檔小倉、可買，卡片不顯示 green/actionable small-buy。
      - 驗證卡片顯示 等RR修復、決策證據、卡關主因、量化差距，並保留 source-error/conflict 與 v20.4.42 attribution regression。

  ## 修改檔案

  - core/generator.py
  - presentation/report.py
  - tests/test_generator_report.py
  - CHANGELOG.md 依指示未直接編輯；本內容供 runner 寫入。

  ## 最小改動策略

  只在 evidence judgment / official Telegram rendering 的直接消費路徑補 fail-closed guard；未改 RR 公式、trend continuation 核心策略、買賣閾值、DB contract、live delivery 或 schema。既有 positive trend continuation 在
  hard gates 通過時仍保留小倉契約。

  ## 契約影響

  - decision_judgment.eligibility_state 契約修正：有 hard blocker 時輸出 blocked。
  - 官方 Telegram summary / funnel / index / card 與 eligibility 同步 fail closed，不再把 blocked 標的列為新倉建議、趨勢延續買入或可買。
  - 既有 stock.*.decision_judgment / report_context["stock_judgments"] 結構未新增欄位。
  - DB schema/write、payload DB contract、live Telegram contract 未變更。

  ## 直接消費者同步

  - formatTelegramMessages official 手機閱讀路徑已同步。
  - Summary / funnel / new-entry suggestion / card renderer 透過 unheld_funnel_state 同步 hard-gate 降級。
  - v20.4.42 未持倉 attribution 兩行格式同步保留。

  ## 未影響模組

  - 未改 strategy decision thresholds。
  - 未改 RR 計算公式或核心 is_valid_entry 策略函式。
  - 未改持倉狀態機、DB schema/RLS/grant/policy/role/index。
  - 未做 DB write、backfill、manual DML 或 live Telegram delivery。
  - 未 commit / push。

  ## 已跑自檢命令

  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/v20_4_43_hard_gate_focused2 arch -arm64 ./.venv/bin/python -m pytest tests/test_generator_report.py -k 'v20_4_43 or
    v20_4_42_postmarket_unheld_gate_attribution_readability_message_list_replay or confirmed_evidence_preserves_limit_lock_chase_hard_blocker or v20_4_39_post_market_mixed_trend_and_prepare_keeps_trend_actionable or
    v20_0_14_post_market_fixture_uses_next_day_plan_semantics or v20_4_18_structural_artifacts_cover_three_fail_closed_cases or v20_4_20_maturity_report or
    v20_4_25_strategy_sample_source_error_blocks_action_without_hiding_available_price or v20_4_16_unheld_card_fails_closed_when_ohlcv_missing or trend_continuation_official_report_has_separate_small_buy_bucket' -q -> 14
    passed。
  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/v20_4_43_hard_gate_pycompile2 arch -arm64 ./.venv/bin/python -m py_compile core/generator.py presentation/report.py tests/test_generator_report.py -> passed。
  - git diff --check -> passed。
  - git status --short -> shows dirty CHANGELOG.md, core/generator.py, presentation/report.py, tests/test_generator_report.py; CHANGELOG.md was not directly edited in this turn.

  ## 殘留風險

  - 未跑 full pytest。
  - 未跑 production runner artifact。
  - 未驗 production DB source artifact。
  - 未做 QA 驗收；Tech 自檢只代表交付前檢查，不代表 QA 通過。

  ## 旁支待辦

  - 若 Owner 要調整 hard blocker 顯示排序或 wording，可另開文案/排序任務。
  - 若要 production source artifact 反證，需由 Architect/QA 走標準 read-only artifact 流程。
