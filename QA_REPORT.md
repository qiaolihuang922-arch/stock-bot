# QA_REPORT:

  ## 測試範圍

  本輪判定為 normal_patch / QA L2，驗證範圍限於 Telegram rendered message 降噪、手機首屏閱讀順序、直接卡片輸出與對應 regression，不擴大到 full repo pytest、replay、backfill 或 production read/write。

  已讀取並比對：

  - TASK.md
  - CHANGELOG.md
  - git diff
  - core/generator.py
  - presentation/report.py
  - tests/test_generator_report.py

  已執行：

  - git diff --check：通過。
  - arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py：146 passed, 225 warnings。
  - QA 補充 probe：自建「可買1 / 僅追蹤1 / 淘汰1」盤中 rendered message，驗證手機首屏與未持倉卡片一致：通過。

  補充說明：第一次未帶 arch -arm64 執行 pytest 時，因主 repo .venv 的 pydantic_core 為 arm64、預設 Python 以 x86_64 載入而 collection error；依 Tech/runner 同口徑使用 arch -arm64 後 full file 通過。

  ## 風險預算與停止條件

  本輪最值得抓的風險：

  1. 前次 blocker 未修乾淨：tests/test_generator_report.py full file 必須通過。已驗證通過；若失敗即阻塞。
  2. 首屏 compact market line 誤導：有可買時必須顯示 可買N，無可買時維持不可推薦語氣。已用既有 tests 與 QA 自建 probe 驗證；若首屏和漏斗不一致即阻塞。
  3. 用顯示修正偷改策略/RR/DB/live delivery。已檢查 diff 只落在 message formatter/render tests，未見 DB schema/write、RR 公式、strategy decision 或 live Telegram path 變更；若出現即阻塞。

  停止條件：TASK/CHANGELOG/diff 不一致、full file pytest 不通、手機首屏仍可誤讀、RR raw value 在淘汰卡片外露、或出現策略/DB/live delivery 越界，均不得通過。

  ## 關聯風險掃描

  TASK 要求的 9 點 rendered-message probe 已在 tests/test_generator_report.py 覆蓋，且 full file 通過。Tech 前次 blocker 的 full file 也已補跑通過。

  diff 可吸收範圍：

  - core/generator.py：cross-day token 去重、未持倉總數/淘汰計數、交易執行短行、presentation deps 補齊。
  - presentation/report.py：partial +0% 文案、不可行動 RR 顯示、compact market overview line、summary exclusion。
  - tests/test_generator_report.py：更新既有 expectation 並新增 Owner 9 點盤中/盤後 probe。

  worktree 殘留：

  - git status --short 只顯示上述三個 tracked modified files。
  - .qa_tmp/ 測試暫存未出現在 git status，未形成可合併 diff。
  - 不建議整包合併，只能吸收本輪三檔與 TASK 對齊的 diff。

  ## 跨區塊語意一致性

  手機閱讀順序檢查結果：

  - Summary 首屏市場行只保留一次市場/R 值，不再有 進攻偏熱｜R3 與 R3 進攻偏熱 雙重說法。
  - 有可買時 QA probe 顯示：市場：中性觀察 R2｜交易執行 1｜持倉風控 0｜未持倉 3（可買1/僅追蹤1/淘汰1）。
  - 無可買場景既有 tests 驗證維持 僅追蹤/淘汰 拆分，不出現像推薦的 追蹤最強 或 新倉：目前沒有可行動候選。
  - Summary 漏斗與未持倉卡片一致：可買 1｜不可追高觀察 0（不可買）｜僅追蹤 1｜淘汰 1。
  - 交易執行使用短行，例如 建準 可買（分批，不追價）、旺宏 減碼（續降優先級），不重複完整風控句。

  ## 使用者誤讀風險

  已反證主要手機誤讀路徑：

  - 淘汰/結構弱不可行動卡片不再露出 RR 3.06，顯示 RR：-（不可行動）。
  - 僅追蹤 summary 不逐行重複 修復中｜連續觀察 1 天，避免看起來像推薦清單。
  - partial 且 modifier=1.0 顯示 證據：partial｜僅輔助參考，不顯示 +0%。
  - 正常 summary 不再混入 背景：、📌 持倉：、重複 市場/結論 等首屏噪音。

  ## 質疑與反證

  主動質疑：compact line 新增 可買N 後，是否會讓一份報文同時有可買、僅追蹤、淘汰時出現首屏計數和漏斗不一致。

  反證：QA 自建盤中 fixture 包含 建準 可買、修復股 僅追蹤、光寶科 淘汰，render 結果同時滿足：

  - 首屏：未持倉 3（可買1/僅追蹤1/淘汰1）
  - 交易執行：建準 可買（分批，不追價）
  - 漏斗：可買 1｜不可追高觀察 0（不可買）｜僅追蹤 1｜淘汰 1
  - 淘汰卡片：RR：-（不可行動）
  - 未出現 追蹤最強、新倉：無有效進場、重複歷史 token。

  ## 未測項目

  未跑 full repo pytest，因 TASK 為 normal_patch / L2 且風險集中在 Telegram rendered message path；已按 Architect 指令跑完整 tests/test_generator_report.py。

  未做 production read-only smoke、DB schema/write、backfill、live Telegram delivery；這些明確屬於非目標或禁止事項。

  未驗證真實 Telegram 發送，只驗證 rendered message list 與手機閱讀順序。

  ## QA 結論

  通過
