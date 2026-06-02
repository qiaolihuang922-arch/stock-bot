# QA_REPORT:

  ## 測試範圍

  本輪驗收 risk_patch_unheld_funnel_overheat_prepare_fix，只驗 TASK/Architect 指定第 3 項：過熱 / RR blocker / 過熱降溫 未持倉不得回傳或計入 可準備，手機閱讀的 summary、漏斗 count、卡片標題、強勢準備摘要需一致；普通非過
  熱強勢準備仍保留 可準備。

  可吸收 diff 僅限：

  - CHANGELOG.md
  - core/generator.py
  - tests/test_generator_report.py

  worktree 殘留：

  - git status --short 只顯示上述 3 個 tracked diff。
  - .qa_tmp/ 內有既存暫存 artifact，但 git ls-files .qa_tmp 為空，未形成 tracked diff。

  ## 風險預算與停止條件

  本輪最值得抓的風險：

  1. 過熱標的仍被 unheld_funnel_state() 算入 可準備，導致 summary / 漏斗 / 卡片矛盾。
  2. format_strong_prepare_summary() 仍把同一過熱標的列入「強勢準備」。
  3. gate 過寬，誤把普通非過熱強勢準備降級成僅追蹤。

  對應驗證：

  - 重跑 Tech 指定測試與完整 tests/test_generator_report.py。
  - 補獨立手機閱讀 probe：同一份報文同時包含 RR blocker 過熱、過熱降溫、普通突破回測準備。

  停止條件：

  - 僅驗上述輸出契約與直接消費者；不擴成 full repo pytest、replay、backfill、production Telegram 或 DB smoke。

  ## 關聯風險掃描

  TASK / CHANGELOG / diff 一致：task_id 與修改範圍一致，CHANGELOG 宣稱只改 unheld_funnel_state() gate、版本與測試，diff 符合。

  實作重點：

  - core/generator.py:4804 對 should_show_overheat_rr_blocker(...)、heat_state HOT/EXTREME、prepare_label == 過熱降溫 先回 等冷卻 / 等回測，再處理 cross_day_prepare_promotion 與 market_mode == 進攻偏熱 的 可準備。
  - core/generator.py:5637 的強勢準備摘要只列 unheld_funnel_state(...) == 可準備 的標的。
  - presentation/report.py:282 卡片主狀態透過同一 funnel helper，舊的 過熱待回測 prepare label 只在 funnel_state == 可準備 時使用。

  未見 diff 觸及 strategy decision、RR 公式、DB schema/write、backfill、live Telegram delivery。

  ## 跨區塊語意一致性

  Tech 測試重跑：

  - targeted pytest：6 passed, 106 deselected, 13 warnings
  - full tests/test_generator_report.py：112 passed, 221 warnings
  - py_compile core/generator.py tests/test_generator_report.py：passed
  - git diff --check：passed

  QA 補充 probe 結果：

  - 熱RR：unheld_funnel_state == 等冷卻
  - 熱標籤：unheld_funnel_state == 等冷卻
  - 普通強勢：unheld_funnel_state == 可準備

  手機閱讀輸出：

  - Summary：未持倉 1 檔不可追高觀察、2 檔僅追蹤
  - 漏斗：可買 0｜不可追高觀察 1（不可買）｜僅追蹤 2｜淘汰 0
  - 僅追蹤拆分：等冷卻 2
  - 強勢準備只列：普通強勢
  - 卡片標題：熱RR / 熱標籤 均為 ⏳ 等冷卻｜過熱觀察，普通強勢為 👀 待回測｜突破回測

  ## 使用者誤讀風險

  已反證同一過熱標的不會在 summary 漏斗 count、卡片標題、強勢準備三處被顯示成 可準備 / 不可追高觀察 / 過熱待回測。本輪輸出會把過熱標的讀成等冷卻或等回測僅追蹤，普通強勢準備仍可被讀成不可追高觀察。

  殘留文案風險：repo 仍有 unheld_non_actionable_prepare_label() 回傳 過熱待回測 的舊分支，但目前只在 funnel_state == 可準備 路徑使用；本輪 probe 未觸發該舊文字。建議作為後續文案清理，不阻塞本輪。

  ## 質疑與反證

  質疑：strong_prepare_bucket() 仍會對 trade_state=EXTENDED 回 過熱降溫，是否會被 summary 強勢準備吃到？
  反證：format_strong_prepare_summary() 先檢查 funnel state；QA probe 中 熱標籤 未出現在強勢準備摘要。

  質疑：新增 gate 是否誤殺普通非過熱準備？
  反證：QA probe 中 普通強勢 仍為 可準備，summary 與卡片仍列 突破回測。

  質疑：RR blocker 過熱是否只改 RR 顯示、不改 funnel？
  反證：QA probe 中 RR=0 且 HOT/EXTENDED 的 熱RR funnel state 為 等冷卻，卡片顯示過熱觀察，不計入 可準備。

  ## 未測項目

  未跑 full repo pytest、production read-only smoke、replay/backfill、DB schema/write、live Telegram delivery；這些均超出 TASK 本輪停止條件。未審全報文所有「追高 / 追蹤」文案，只驗本輪直接消費者。

  ## QA 結論

  通過
