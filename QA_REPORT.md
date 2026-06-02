# QA_REPORT:

  ## 測試範圍

  - 任務尺寸 / QA 分級：normal_patch / L2。驗證限於 06/02 盤中 v20.4.25 A1/A2/A3 報文硬衝突；未擴成 full pytest、replay、backfill、production write 或 live Telegram。
  - 已讀：TASK.md、CHANGELOG.md、git diff、core/generator.py、presentation/report.py、tests/test_generator_report.py。
  - 可吸收 diff：CHANGELOG.md、core/generator.py、presentation/report.py、tests/test_generator_report.py。
  - worktree 殘留：git status --short 只顯示上述 4 個 tracked modified；.qa_tmp/ 有既存暫存 artifacts，但不在 tracked diff 中，本輪不建議整包合併。
  - 清理 / 瘦身 / refactor 證據表：不適用，本輪不是清理任務。

  ## 風險預算與停止條件

  本輪最值得抓的風險：

  1. A1 手機首屏誤讀：不可買 / 不可追高未持倉仍以「可準備 / 可買 / 推薦」主標籤呈現。
      - 驗證：重跑 Tech tests，另以獨立 render probe 檢查未持倉卡片 title line。
      - 停止條件：任一不可買卡片主標籤含「可準備 / 可買 / 推薦」即 blocked。
  2. A2/A3 跨區塊硬衝突：同一持倉主行動或排序在卡片、持倉風控檢查、詳情索引不一致。
      - 驗證：按手機閱讀順序抽取 holding card order、control order、index order，並抽取每檔 title / decision / control 主行動。
      - 停止條件：任一序列或主行動不一致即 blocked。
  3. 範圍外回退：誤改 strategy decision、RR、holding_status、DB schema/write、live Telegram 或 services/analysis.py。
      - 驗證：git diff --name-only、git diff -- services/analysis.py、diff keyword scan。
      - 停止條件：出現上述範圍外產品邏輯 / DB / live delivery diff 即 blocked。

  ## 關聯風險掃描

  - TASK / CHANGELOG / diff 一致：CHANGELOG 宣稱修改檔案與 git diff --name-only 一致。
  - 版本：core/generator.py VERSION 已由 v20.4.24 升至 v20.4.25，符合不得回退契約。
  - 未改 services/analysis.py：git diff -- services/analysis.py 無輸出。
  - 未見 DB schema/write、live Telegram delivery、RR 計算、strategy decision 測試期待值變更；實際 diff 集中在報文顯示 helper、formatter、snapshot/probe tests。
  - 注意：position_summary_action 一般續抱顯示統一成「續抱觀察」，屬 A2 使用者可見主行動收斂，未看到策略 decision 本身改動。

  ## 跨區塊語意一致性

  Tech 自檢：

  - pytest -q tests/test_generator_report.py：106 passed，217 warnings。
  - py_compile core/generator.py presentation/report.py tests/test_generator_report.py：passed。
  - git diff --check：passed。
  - warnings 來自既有第三方 deprecation / Python 版本提示，非本輪阻塞。

  QA 額外手機閱讀 probe：

  - 渲染 06/02 盤中訊息：message_count 3，仍是持倉 / 未持倉 / summary message list。
  - 未持倉不可買 / 不可追高 title：
      - 【台積電 2330】👀 不可追高觀察｜漲停鎖價
      - 【台達電 2308】👀 過熱待回測｜過熱降溫
      - title line 未含「可準備 / 可買 / 推薦」。
  - 持倉排序：
      - card order：['英業達', '技嘉']
      - control order：['英業達', '技嘉']
      - index order：['英業達', '技嘉']
  - 同一持倉主行動：probe 抽取 title / decision / control 三處一致。

  ## 使用者誤讀風險

  - Summary 仍明確輸出「新倉：無有效進場」，未把不可買標的包裝成可行動推薦。
  - 漏斗與詳情索引使用「不可追高觀察」口徑，不再以主標籤「可準備」承接不可買 / 不可追高數量。
  - 持倉卡片、風控檢查、詳情索引能用相同序列對回，手機上下滑不會把持倉順序讀錯。

  ## 質疑與反證

  - 質疑：Tech tests 新增了 A1/A2/A3，但可能只驗單點文字，沒有按手機閱讀順序看整份 rendered messages。
  - 反證：QA 獨立 render 同時含 2 檔持倉與 2 檔不可買未持倉，按 summary -> holding cards -> unheld cards -> control/index 抽取並比對，通過。
  - 質疑：CHANGELOG 宣稱未碰策略 / DB / live delivery，可能與 diff 不一致。
  - 反證：diff name 只有報文與測試相關檔；services/analysis.py 無 diff；未見 schema/write/live delivery 相關檔案變更。

  ## 未測項目

  - 未跑 full repo pytest、replay、backfill、production read-only smoke；TASK L2 與本輪非目標不要求。
  - 未驗 live Telegram delivery、DB write path、production source-of-truth；TASK 明確禁止 / 非目標。
  - 未處理 Owner 所稱降噪第二批、全量詞彙盤點、全報文瘦身；列為後續風險，不阻塞本輪。

  ## QA 結論

  通過
