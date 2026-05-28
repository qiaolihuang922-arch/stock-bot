# QA_REPORT:

  ## 測試範圍

  依據 TASK.md、CHANGELOG.md、git diff 驗證 Tech 第三輪候選 diff。

  實測命令：

  TMPDIR=.qa_tmp PYTHONPATH=.qa_tmp:$PWD arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py tests/test_notifier.py -q

  結果：46 passed, 21 warnings

  補充檢查：

  - git diff --check：通過，無 whitespace error。
  - 手機長報文 fixture：英業達已減碼、建準僅追蹤、群創淘汰、光寶科淘汰。
  - git status --short：僅有 CHANGELOG.md、core/generator.py、tests/test_generator_report.py 三個 task-scoped 修改。

  ## 關聯風險掃描

  可吸收候選 diff：

  - core/generator.py：v20.0.11、summary/持倉風控/隔日計畫文案、交易執行與觀察分離、淘汰主因補充。
  - tests/test_generator_report.py：同步 v20.0.11 與長報文契約。
  - CHANGELOG.md：Tech 交付摘要。

  worktree 殘留：

  - 未見其他 tracked 修改；不建議「整包合併」以外的無關內容，Architect 合併時仍應只吸收上述 task-scoped diff。
  - core/generator.py 仍有內部 明日未修復降級 trigger 字串，但 QA 長報文輸出確認未出現在 summary 或持倉 detail card，只用於產生條件式 隔日計畫 候選。

  ## 跨區塊語意一致性

  手機長報文檢查通過：

  - Header 顯示 【05/28 盤中｜v20.0.11】。
  - Summary 無 明日未修復 / 隔日未修復 / 今日盤中執行清單。
  - 持倉 detail card 無 明日未修復 / 隔日未修復。
  - 今日盤中交易執行顯示 無新增下單。
  - 詳情索引顯示 交易執行 0，未把英業達剩餘觀察或建準追蹤算成交易。
  - 英業達完整已執行句只在 summary 出現 1 次，且無 待執行｜減碼 25%、停利 25%、賣 25%。
  - 群創與光寶科均為 淘汰｜突破失敗；補充原因未覆蓋主因。
  - 漏斗維持：未持倉總數 3，僅追蹤 1，淘汰 2，拆分可對上。

  ## 使用者誤讀風險

  Owner 手機第一屏現在能先看到：

  - 今日交易執行：無新增下單。
  - 英業達已執行且不重複下單。
  - 持倉風控檢查與交易執行分區。
  - 未持倉僅追蹤與淘汰，不像可買推薦。

  未發現會讓 Owner 誤判買、賣、加碼、停損或追蹤優先級的舊詞或重複噪音。

  ## 質疑與反證

  主動反證點：

  - 質疑 Tech 只說內部舊字串仍存在但已清洗輸出：QA 用長報文實際輸出反證，summary/detail card 均無舊詞。
  - 質疑觀察項仍可能被交易統計吃進去：QA 檢查 交易執行 0 與 無新增下單，英業達剩餘觀察未進交易執行。
  - 質疑英業達已執行長句重複：QA 計數完整長句為 1 次。
  - 質疑淘汰主因不一致：QA 同時檢查 summary 淘汰主因與未持倉卡，群創/光寶科一致為突破失敗。
  - TASK.md / CHANGELOG.md / diff 未見阻塞性不一致；本輪不是清理/瘦身/refactor 任務，path/claim/evidence/risk/action 證據表不適用。

  ## 未測項目

  未測前端預覽頁 http://127.0.0.1:5173/，本輪未啟動前端服務；因直接 formatter 與 notifier 測試已通過，且未改前端消費契約，接受。

  未執行 full pytest、replay/backfill dry-run、live Telegram、live Supabase write；符合本輪禁止事項與 L2 範圍。

  ## QA 結論

  通過
