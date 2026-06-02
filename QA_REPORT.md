# QA_REPORT: 持倉風控檢查完整列出全部持倉

  ## 測試範圍

  本輪 TASK 為 normal_patch、QA L2；驗證限於 Telegram 第三則「持倉風控檢查」使用者可見輸出、版本同步、直接 formatter 契約與相關報文測試，未擴成 full repo pytest / replay / backfill / production smoke。

  已讀取並比對：

  - TASK.md
  - CHANGELOG.md
  - git diff -- core/generator.py tests/test_generator_report.py CHANGELOG.md
  - 直接呼叫點：presentation/report.py

  執行驗證：

  - git diff --check：passed
  - arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py::GeneratorReportTest::test_intraday_mobile_a3_holding_order_matches_cards_control_and_index：1 passed
  - arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py：116 passed，225 warnings
  - QA 自補 helper probe：預設 6 檔完整列出、不含「另有」/「見詳情」；顯式 limit=5 仍維持 5 筆加截斷提示相容行為。

  ## 風險預算與停止條件

  本輪最值得抓的風險：

  1. 第三則仍只列前 5 檔，或第 6 檔以上靠「另有 / 見詳情」藏到 detail。
      - 驗證：6 檔 fixture、第三則 control section、直接 helper probe。
      - 停止條件：少於 6 筆或出現截斷提示即 blocked。
  2. 持倉風控排序與第一則持倉卡 / 第三則 detail index 不一致，造成 Owner 手機閱讀交叉對照錯位。
      - 驗證：測試抽出持倉卡順序、control 順序、detail index 順序並比對。
      - 停止條件：任一順序不一致即 blocked。
  3. CHANGELOG / TASK / diff 再次不同步，或 diff 擴到策略、RR、DB write、未持倉漏斗。
      - 驗證：文件與 diff 對照、呼叫點掃描。
      - 停止條件：跨文件或實作範圍不一致即 blocked / conditional pass。

  ## 關聯風險掃描

  TASK、CHANGELOG、git diff 已一致指向「持倉風控檢查完整列出全部持倉」。可吸收 diff 為：

  - CHANGELOG.md：本輪 handoff 同步。
  - core/generator.py：版本 v20.4.28；format_holding_control_checklist 預設 limit=None；預設不再輸出持倉風控截斷提示；holding control 順序改沿用輸入 holding_items。
  - tests/test_generator_report.py：版本期望同步；6 檔以上手機閱讀 probe 補強。

  未發現 strategy decision、主行動判斷、RR、DB schema/write path、live delivery、未持倉漏斗邏輯 diff。git status --short 只有上述 3 個 tracked file dirty；.qa_tmp/ 為測試暫存/既有暫存，不屬可吸收產品 diff。

  ## 跨區塊語意一致性

  使用者手機閱讀順序已檢查：

  - 第一則「持倉標的」持倉卡順序由 sort_position_summary 產生。
  - 第三則「持倉風控檢查」透過同一份 holding_items 產生，不再另用 holding_execution_priority 重排。
  - 第三則 📎 詳情索引：持倉 ... 也沿用同一 holding_items。
  - 測試驗證 6 檔時 card_order == control_order == index_order，且 control section 含第 6 筆。

  版本字串已由 v20.4.27 升至 v20.4.28，測試同步覆蓋 header / evidence version / artifact generator_version。

  ## 使用者誤讀風險

  主要誤讀路徑是 Owner 在第三則看到 5 筆後，以為其餘持倉只能到詳情找，或「另有 N 項持倉風控見詳情」被理解為第三則沒有完整風控。現有 diff 已移除預設截斷，6 檔 fixture 第三則直接列出第 6 檔，且 control section 不含「另有」
  與「見詳情」。

  殘留風險：完整列出全部持倉會拉長第三則訊息；這是 TASK 明確要求的結果，Telegram 長訊息切分治理不屬本輪。

  ## 質疑與反證

  QA 未只重跑 Tech 自檢，另補直接 helper 反證：

  - 預設呼叫 format_holding_control_checklist(holding_items, report_phase="盤中")：6 檔全部輸出，最後一筆為第 6 檔，無截斷提示。
  - 顯式呼叫 format_holding_control_checklist(..., limit=5)：仍輸出 5 筆與「另有 1 項持倉風控見詳情」，證明 public helper 參數相容性保留，變更只影響預設使用者可見路徑。

  質疑排序回退：diff 移除 holding_control_items 內的 execution priority 排序；呼叫點確認持倉卡、control、detail index 都吃排序後的同一份 holding_items，測試反證一致。

  ## 未測項目

  未跑 full repo pytest、production read-only smoke、live Telegram、DB write/backfill、Telegram 極端長訊息切分。依 TASK 的 normal_patch / L2 與本輪停止條件，這些不是必要驗收範圍。

  warnings 為既有第三方 deprecation / Python 版本提示；未在本輪處理。

  ## QA 結論

  通過
