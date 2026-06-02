# CHANGELOG: risk_patch_unheld_funnel_overheat_prepare_fix

  ## 任務尺寸與風險

  - 任務尺寸：risk_patch
  - 風險：影響未持倉 funnel 分類、summary count、卡片狀態與使用者可見 Telegram 版本；未改策略 decision、RR 公式、DB 或 live delivery。

  ## 修改內容

  - unheld_funnel_state() 新增過熱 prepare gate：
      - should_show_overheat_rr_blocker(result, holding=False) 為 true 時，不再回傳 可準備。
      - heat_state 為 HOT / EXTREME 時，不再回傳 可準備。
      - strong_prepare_bucket() label 為 過熱降溫 時，不再回傳 可準備。
      - 上述標的改走既有 等冷卻 / 等回測 僅追蹤分類。
  - 保留非過熱普通強勢準備，例如 突破回測，仍可在 R3 進攻偏熱 下回傳 可準備。
  - 報文版本由 v20.4.25 升為 v20.4.26。
  - 補/更新可重跑 probe，覆蓋過熱 RR blocker、HOT、過熱降溫、EXTREME 漲停與普通強勢準備不誤降級。

  ## 修改檔案

  - core/generator.py
  - tests/test_generator_report.py

  ## 最小改動策略

  - 只在 unheld_funnel_state() 內調整分類 gate，沿用既有 tomorrow_watch_state()、should_show_overheat_rr_blocker()、strong_prepare_bucket() 與既有 funnel buckets。
  - 未新增 funnel bucket，未重構 summary / card renderer。
  - 測試只同步受分類與版本影響的既有報文斷言，並新增直接分類 probe。

  ## 契約影響

  - unheld_funnel_state() public helper 行為變更：
      - 過熱 / RR blocker / 過熱降溫 未持倉不再回傳 可準備。
      - 這類標的會計入 等冷卻 或 等回測，因此 summary、漏斗 count、詳情索引、卡片排序會同步反映為僅追蹤。
  - Telegram header / report context version 同步為 v20.4.26。
  - 未改 payload shape、DB contract、message list 數量、RR 顯示公式或 strategy decision。

  ## 直接消費者同步

  - build_unheld_funnel()、today_conclusion_text()、format_execution_checklist()、format_unheld_funnel()、detail_index_text() 皆透過 unheld_funnel_state() 自動同步新分類。
  - formatTelegramUnheldCard() 透過同一 helper 顯示 等冷卻 / 等回測 卡片主狀態，避免卡片過熱但漏斗仍算可準備。
  - format_strong_prepare_summary() 只列仍屬 可準備 的普通準備標的，過熱標的不再列入強勢準備摘要。

  ## 未影響模組

  - 未改 services/analysis.py
  - 未改 strategy decision / action 產生邏輯
  - 未改 RR 計算公式或 blocker 定義
  - 未改 DB schema / write path / backfill
  - 未執行 live Telegram 或 Supabase write
  - 未處理其他清單項

  ## 已跑自檢命令

  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py -k "overheat_prepare or overheat_blocker or r3_hot_market_adds_prepare_layer
    or low_volume_limit_up_prepare or r3_hot_prepare_overflow or mobile_a1_unheld or unheld_funnel_groups"：6 passed，13 warnings
  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py：112 passed，221 warnings
  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m py_compile core/generator.py tests/test_generator_report.py：passed
  - git diff --check：passed

  ## 殘留風險

  - 本輪只修未持倉 funnel 過熱 prepare 分類；未審全報文所有「追高 / 追蹤」文案。
  - warnings 皆為既有第三方 deprecation / Python 版本警告，非本輪新增。
  - Tech 自檢不代表 QA 通過。

  ## 旁支待辦

  - 其他 Owner 清單項另開任務處理。
  - 若後續要統一「過熱待回測」與 等冷卻 / 等回測 的可見命名，可另開文案/漏斗命名任務。
  - 若要完整驗 production 實際報文，需由 QA / Architect 依標準 read-only artifact 或 runner 流程處理，不在本輪 Tech 實作內。
