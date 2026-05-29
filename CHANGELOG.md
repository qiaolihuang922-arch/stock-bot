# CHANGELOG:

  ## 任務尺寸與風險

  - TASK 任務尺寸：risk_patch。
  - Phase 1 候選 diff 風險：risk_patch，因為接入跨日 DB / local event context，會影響 Telegram / CLI 使用者可見排序、summary、持倉行動去重與歷史證據說明。
  - 本輪 Tech 動作：process，只補完整交付說明；依 Architect 指令未修改產品代碼或測試，未 commit / push。

  ## 修改內容

  - 新增 Phase 1 cross-day context 建構邏輯：
      - 產生 symbol、source_status、source_of_truth、previous_state、previous_action、previous_action_date、consecutive_observe_days、repair_status、failure_status、historical_evidence_weight、weight_reason、
        dedupe_guard、allowed_effects、forbidden_effects。
      - DB / local source 缺失時 fail closed，不補 fake previous state、fake consecutive days、fake evidence weight、fake today event。
      - historical_evidence_weight 有界在 -2..+2。
      - forbidden_effects 包含 cannot_flip_to_buy_alone、cannot_override_hard_stop、cannot_fake_execution、cannot_confirm_market_evidence。
  - core/generator.py 接入 cross-day context：
      - VERSION 升為 v20.4.0，formatter / notifier 測試期望同步。
      - 允許 context 影響同分組排序、summary wording、prepare promotion、duplicate action suppression、risk note。
      - 淘汰但近期修復 / evidence 偏正者可提升到可準備 / 追蹤呈現，但不會單獨變成可買或交易執行。
      - 已停利 / 已減碼的同級重複建議會轉為停利後觀察 / 減碼後觀察。
      - 今日買入後轉弱預設顯示新倉風控觀察，不無脈絡反向減碼；硬風控 / 硬停損仍可覆蓋。
      - 個股卡與 summary 增加歷史追溯短句。
  - QA blocker 修復：
      - 本次交付說明已把 untracked 新檔納入候選範圍：services/cross_day_context.py、tests/test_cross_day_context.py。
      - CHANGELOG 不再只描述窄修補，改為累計覆蓋 Phase 1 全部候選 diff。
  - 測試覆蓋：
      - 新增 cross-day context missing-source 與 ready-history fixture。
      - 新增 generator 報文 fixture：連續修復只升準備不買、停利同級不重複、歷史減碼不壓過硬風控、今日買入後轉弱不無脈絡反向減碼。
      - 同步 v20.4.0 header 期望。
      - 同步 market theme evidence / notifier header 測試。

  ## 修改檔案

  - services/cross_day_context.py：新增 cross-day context 建構、source-of-truth 標示、fail-closed default、history/event/weight/dedupe guard 計算。
  - core/generator.py：版本升為 v20.4.0；接入 context；更新排序、summary、持倉卡、未持倉卡、同級停利/減碼去重、新倉風控觀察 guard。
  - tests/test_cross_day_context.py：新增 context contract / missing-source / ready-history 測試。
  - tests/test_generator_report.py：新增 Phase 1 報文 fixture 並同步 v20.4.0 header。
  - tests/test_market_theme_evidence.py：同步 v20.4.0 header，保留 missing-source market evidence fail-closed 驗證。
  - tests/test_notifier.py：同步 v20.4.0 header，確認最後一則 summary header 不被 notifier 改寫。

  ## 最小改動策略

  - 只新增 cross-day context helper 與 generator 直接消費點；未重寫 analysis engine、store layer、watchlist、DB schema 或 Telegram delivery。
  - 不改核心 BUY / SELL / RR / 停損停利門檻。
  - 不把 DB 歷史權重當成可買條件，只作排序、摘要、準備層提升、同級動作去重與詳情追溯。
  - untracked 新檔是本候選 diff 的一部分，不是旁支雜檔。

  ## Source-of-truth 與 Fail-closed

  - positions：沿用既有 production holding source / position store contract；本候選 diff 未新增 positions fallback。source-error / missing-source 不得回全 watchlist 0 股或產生假持倉結論。
  - position_events：position_events table 是 execution/history truth；core/generator.py 另把本輪已載入的 local today_position_events 傳入 context 作同日事件 guard。source-error / missing-source 不得回全 0 event
    summary；只有可信 today events 或 DB rows 才可產生 same_day_executed / prior_* guard。
  - daily_signal_snapshot：cross-day state candidate；缺失只代表無 snapshot 證據，不代表狀態不存在。
  - strategy_feature_snapshots：previous classification / watch category candidate；不得用過期 feature 覆蓋當日硬門檻。
  - strategy_outcome_metrics：historical weight candidate；只調整 evidence weight / sort priority / wording，不單獨改買賣門檻。
  - strategy_classification_audit：目前只列為 Phase 1 source candidate；缺資料不得假設前次分類。
  - signal_runs / signal_items / signal_outcomes：本候選 diff 未接入為 runtime truth；缺失不生成 fake evidence。
  - local store path：只透過既有 today_position_events input 作同日 guard；標示為 local_position_events，不默默優先於 production DB truth。
  - DB client 缺失：回 missing-source context。
  - DB query error：無 ready evidence 時回 source-error，不輸出假歷史。
  - 有 client 但無可信 rows：回 insufficient-data，權重 0、前次 unknown、連續天數 0。

  ## 契約影響

  - 使用者可見版本 header：v20.4.0。
  - 新增 public-ish formatter helper 行為：
      - cross_day_context
      - cross_day_ready
      - cross_day_sort_adjustment
      - cross_day_repair_label
      - cross_day_detail_line
      - cross_day_prepare_promotion
      - cross_day_duplicate_action
      - format_cross_day_tracking_summary
  - message list / formatter output 會變更：
      - summary 可新增「追蹤最強」cross-day 修復提示。
      - 持倉卡與未持倉卡可新增「歷史：...」追溯行。
      - 同級停利 / 減碼重複建議可改成觀察文案。
      - 未持倉 funnel 可因 cross-day repair promotion 進入可準備，但不得變可買。
  - payload / DB write / schema：未改。
  - Telegram live delivery：未執行、未改 delivery path。

  ## Allowed / Forbidden Effects

  - allowed_effects：
      - sort_priority
      - summary_wording
      - prepare_promotion
      - duplicate_action_suppression
      - risk_note
  - forbidden_effects：
      - cannot_flip_to_buy_alone
      - cannot_override_hard_stop
      - cannot_fake_execution
      - cannot_confirm_market_evidence
  - 實作限制：
      - DB 歷史不可單獨造成不可買 -> 可買。
      - 淘汰 / 可準備不可因歷史權重進入交易執行清單。
      - 硬風控 / 硬停損優先於歷史同級去重。
      - 缺來源時不輸出連續天數、已執行事件、持倉、價格或 confirmed evidence。

  ## 直接消費者同步

  - core/generator.py 已同步消費 build_cross_day_contexts()，並把 context 寫入 results_map[name]["cross_day_context"]。
  - Telegram Owner 報文已同步：summary、持倉卡、未持倉卡、行動去重與歷史追溯行。
  - tests/test_generator_report.py 已同步直接 formatter 消費者與手機閱讀順序 fixture。
  - tests/test_notifier.py 已同步 notifier 對最後一則 summary header 的版本期望。
  - tests/test_market_theme_evidence.py 已同步 v20.4.0 header，並保留 market evidence missing-source fail-closed 路徑。
  - services/analysis.py 未在本候選 diff 中直接修改；Phase 1 目前由 generator 在 render 前消費 context。
  - services/position_store.py、services/signal_store.py、services/daily_snapshot_store.py、services/strategy_evidence.py 未在本候選 diff 中修改；未新增平行 write path。

  ## 未影響模組

  - 無 DB schema / migration / table / column / index diff。
  - 無 live Supabase write。
  - 無 live Telegram delivery。
  - 無正式 backfill。
  - 無 watchlist diff。
  - 無核心 BUY / SELL / RR / 過熱 / 漲停不追 / 停損停利門檻 diff。
  - 無 callback Edge Function diff。
  - 無 replay / production DB 連線驗證。

  ## 已跑自檢命令

  - arch -arm64 .venv/bin/python -m pytest tests/test_cross_day_context.py tests/test_generator_report.py tests/test_market_theme_evidence.py tests/test_notifier.py
      - 結果：89 passed, 13 warnings。
  - git diff --check
      - 結果：通過，無輸出。
  - git status --short
      - 結果：候選 diff 為 core/generator.py、tests/test_generator_report.py、tests/test_market_theme_evidence.py、tests/test_notifier.py，候選 untracked 新檔為 services/cross_day_context.py、tests/
        test_cross_day_context.py。

  ## 殘留風險

  - 未驗證 production DB 真實資料品質；目前只驗證缺來源、error、insufficient-data 與 fixture rows。
  - strategy_classification_audit、signal_runs、signal_items、signal_outcomes 未成為實際 runtime truth；若後續要納入，需要另開任務定義欄位可信度與衝突優先級。
  - services/analysis.py 未直接消費 context；目前使用者可見 Phase 1 效果集中在 generator render 前後。
  - 缺來源時會犧牲歷史詳情追溯，以 fail closed 優先，符合本輪契約但可能降低資訊量。
  - warnings 來自既有第三方套件 / Python 版本警告，未在本輪處理。

  ## 旁支待辦

  - 若 Owner 要把 cross-day context 往 analysis decision 層前移，需要 PM 另定義策略優先級、直接消費者與不變性驗收。
  - 若要接入 signal_runs / signal_items / signal_outcomes / strategy_classification_audit，需要另定義 source precedence、欄位缺失行為與測試 fixture。
  - 若要驗證 production DB 真實資料，需要另行批准非 live write 的讀取驗證範圍；本輪未做 live write、正式 backfill 或 Telegram delivery。
