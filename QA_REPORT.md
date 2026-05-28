# QA_REPORT:

  ## 測試範圍

  - 依據：TASK.md、CHANGELOG.md、git diff、core/generator.py、services/analysis.py、相關測試 diff。
  - 候選 diff 範圍：core/generator.py、services/analysis.py、tests/test_analysis_engine.py、tests/test_generator_report.py、CHANGELOG.md。
  - 可吸收 diff：上述 5 個檔案與本輪任務一致，可作為候選審核範圍。
  - worktree 殘留：git status --short 只顯示上述 5 個 tracked modified；QA 未修改 tracked file。.qa_tmp/ 僅作測試暫存，不應作為合併內容。

  實測命令：

  TMPDIR=$PWD/.qa_tmp PYTHONPATH=$PWD/.qa_tmp:$PWD arch -arm64 .venv/bin/python -m pytest tests/test_analysis_engine.py tests/test_generator_report.py tests/test_notifier.py -q

  結果：76 passed, 21 warnings

  QA 追加負面/對照案例：用 inline Python fixture 驗證 市場弱+RR不足、結構弱+RR不足、突破失敗+RR不足、弱反彈+RR不足 四類真正淘汰，以及非淘汰 RR不足 對照。結果通過。

  ## 關聯風險掃描

  - TASK.md / CHANGELOG.md / diff 一致：本輪確實修改策略狀態、觀察天數傳遞、未持倉分類與 Telegram 顯示文案，未見任務外 DB schema、watchlist、live send、正式 backfill 改動。
  - 直接消費者已檢查：formatTelegramMessages()、formatTelegramUnheldCard()、summary 漏斗、unheld_funnel_state()、tomorrow_watch_state()、holding_status() 呼叫鏈。
  - VERSION = "v20.0.9" 仍存在於 core/generator.py，測試也回歸 header 未回退。
  - 清理/瘦身/refactor 證據表要求不適用：本輪不是清理任務。

  ## 跨區塊語意一致性

  按 Owner 手機閱讀順序檢查：

  - Header：仍為 v20.0.9。
  - Summary 主因：真正淘汰且 RR不足時，主因顯示 市場弱 / 結構弱 / 突破失敗 / 弱反彈待確認，未顯示 RR不足。
  - 未持倉卡主標：真正淘汰顯示 ⛔ 淘汰｜<淘汰主因>，未被 RR不足搶主標。
  - 買點行：真正淘汰顯示 等市場轉強、等結構修復、等重新轉強 或 重新轉強前不列優先，未出現 等RR達標。
  - 明日觸發：真正淘汰顯示 重新轉強前不列優先，未出現 RR修復至達標。
  - 非淘汰 RR不足 對照：仍顯示 等RR修復、等RR達標、RR修復至達標，不追高，符合任務要求。
  - 漏斗與降噪：局部回歸測試覆蓋未持倉母集合、僅追蹤拆分、淘汰主因不反覆點名；未見回退。

  ## 使用者誤讀風險

  本輪關鍵誤讀路徑已被修正：真正淘汰標的不再因 RR不足被手機第一屏或卡片讀成「只要 RR 修復就可買」。非淘汰 RR不足 仍維持等RR修復，因此不會把可追蹤標的誤降為淘汰。

  仍需注意：若 production position events 缺少可估算今日買賣比例的欄位，已減碼/已買入狀態仍可能無法被策略推導；這是 CHANGELOG.md 已揭露的資料完整性殘留，不是本輪 diff 可完全消除的 formatter 問題。

  ## 質疑與反證

  - 質疑 Tech 是否只修單一 市場弱+RR不足：QA 追加覆蓋 結構弱、突破失敗、弱反彈，均未露出 RR 修復語意。
  - 質疑是否只修買點行、漏掉明日觸發：QA 檢查 明日觸發，真正淘汰均為 重新轉強前不列優先。
  - 質疑是否破壞非淘汰 RR不足：QA 對照 fixture 確認仍進 等RR修復。
  - 質疑是否回退既有直接消費者：重跑 tests/test_notifier.py 與 formatter/analysis 測試，message list 消費者未破壞。
  - 質疑是否整包合併風險：目前 tracked diff 僅任務相關 5 檔；仍建議 Architect 合併時只吸收候選 diff，不把 .qa_tmp/ 或任何工作暫存納入。

  ## 未測項目

  - 未執行 full pytest、replay/backfill dry-run、live Telegram delivery、live Supabase write；依 TASK.md 非目標與禁止事項可接受。
  - 未連 production position events 實資料驗證；本輪以策略/formatter fixture 與 message contract 驗證為主。

  ## QA 結論

  通過
