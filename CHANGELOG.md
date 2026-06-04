# CHANGELOG: v20.4.41 盤後未持倉 gate attribution 可讀性修正

  ## 任務尺寸與風險

  - tiny_patch。
  - QA blocker 返工，只修 formatter gate attribution 與 focused official message-list replay 測試；不改策略、RR、can_buy、is_valid_entry、DB 或 live delivery。

  ## 修改內容

  - 修正 _unheld_buy_gap_line：距突破 X%/需<=4% 只在 distance > 4 時列入「到達可買差距」。
  - 補 official formatTelegramMessages message-list replay 負面案例：RR不足且 distance=2 的非可買卡，只顯示 RR gap，不顯示 距突破 2%/需<=4%。
  - 保留 v20.4.41 既有候選契約：可買 / trend_continuation 不顯示差距；distance=6 仍顯示距突破；FAILED_BREAKOUT、post-market prepare、EXTREME/HOT、raw enum、RR不足不誤顯盤後待確認不回退。

  ## 修改檔案

  - presentation/report.py
  - tests/test_generator_report.py
  - core/generator.py 保留既有 v20.4.41 版本候選 diff，未回退。

  ## 最小改動策略

  - 只改距突破 gate 條件與同一 focused replay 測試。
  - 未新增 helper、未重構 formatter、未調整排序 / 分組邏輯。
  - 未直接編輯 CHANGELOG.md；本內容供 runner 寫入。

  ## 契約影響

  - 使用者可見版本維持 v20.4.41。
  - message list 文案契約微調：已達標突破距離 <=4% 不再被列為「到達可買差距」。
  - 未改函式回傳結構、payload shape、message list 順序、報文分組、DB 寫入或 CLI 輸出。

  ## 直接消費者同步

  - 同步 tests/test_generator_report.py 的 official formatTelegramMessages / message-list replay assertion。
  - 覆蓋層級：official formatter / message-list replay；未只停在 helper fixture。

  ## 未影響模組

  - 未改策略決策、RR 計算、can_buy、is_valid_entry。
  - 未改 DB schema / RLS / grant / policy / role / read-write path。
  - 未執行 live Telegram、live Supabase write、正式 backfill。
  - 未改持倉建議、買賣 / 加減碼、停損停利策略。

  ## 已跑自檢命令

  - arch -arm64 ./.venv/bin/python -m pytest tests/test_generator_report.py -k 'v20_4_41_postmarket_unheld_gate_attribution_readability_message_list_replay or confirmed_evidence_preserves_limit_lock_chase_hard_blocker or
    v20_4_39_post_market_mixed_trend_and_prepare_keeps_trend_actionable or v20_0_14_post_market_fixture_uses_next_day_plan_semantics' -q -> 4 passed。
  - PYTHONPYCACHEPREFIX=/private/tmp/v20_4_41_pycache_qa_blocker arch -arm64 ./.venv/bin/python -m py_compile core/generator.py presentation/report.py tests/test_generator_report.py -> passed。
  - git diff --check -> passed。

  ## 殘留風險

  - 未跑 full pytest。
  - 未跑 production runner artifact。
  - 未做 live Telegram / DB read-write 驗證。
  - Tech 自檢不代表 QA 通過。

  ## 旁支待辦

  - 無本輪必要旁支；若 Owner 要更細 gate ranking / wording，需另開任務。
