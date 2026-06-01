# QA_REPORT: tg-message-order-v20.4.12

  ## 測試範圍

  - 任務尺寸 / QA level：tiny_patch / L1；驗證範圍維持在 Telegram message list order、版本字串、直接 sender 消費順序，不擴大到 full replay / backfill / production evidence 矩陣。
  - 讀取文件：`TASK.md`、`CHANGELOG.md`。
  - 檢查 diff：`core/generator.py`、`tests/test_generator_report.py`、`tests/test_market_theme_evidence.py`；另只讀 `services/notifier.py` 作直接 consumer list-order 風險檢查。
  - Worktree 狀態：目前 modified 只有 `CHANGELOG.md` 與 scoped 三個檔案；未見 unrelated residual。可吸收 diff 為 scoped code/test order/version 變更，`CHANGELOG.md` 為一致交付摘要；未建議整包合併。
  - QA 未修改任何 tracked file，未做 live Telegram 或 DB write。

  ## 風險預算與停止條件

  - 風險 1：手機閱讀順序仍 summary first 或 summary 插在 action body 中間。驗證：diff 與測試確認 messages[0] 持倉、messages[1] 未持倉、messages[2] summary + Evidence Compact。
  - 風險 2：sender / consumer 端重新排序或 reply markup 影響 list delivery。驗證：只讀 `services/notifier.py` 與 mock `send_many()`，確認 enumerate 原 list 逐則送出。
  - 風險 3：排序修正順手改到策略、假 evidence、DB/write/live delivery。驗證：scoped diff 未碰策略 / DB / sender；既有相關測試與 integrity assertions 通過。
  - 停止條件：完成 L1 scoped tests、版本殘留掃描、直接 consumer order 反證；不進行 live Telegram、production write、DB schema 檢查或 full replay。

  ## 關聯風險掃描

  - `core/generator.py`：VERSION 已由 v20.4.11 升為 v20.4.12；`formatTelegramMessages()` 改為 append holdings、unheld、summary+evidence。未改回傳型別，仍為 string list。
  - `services/notifier.py`：`send_many()` 以 `for index, message in enumerate(messages)` 原序送出，未看到 consumer 端把 summary 移到第一則；reply markup 仍掛最後一則，屬 CHANGELOG 已列旁支風險，不阻塞本輪 order 修正。
  - `rg -n "v20\\.4\\.11|v20\\.4\\.12" core tests services -g '*.py'`：使用者可見版本已是 v20.4.12；v20.4.11 僅作負向斷言出現。
  - `git diff --check -- core/generator.py tests/test_generator_report.py tests/test_market_theme_evidence.py`：通過。
  - 未見 DB schema、DB write path、production writer、live Telegram delivery 相關 diff。

  ## 跨區塊語意一致性

  - TASK 要求：持倉 -> 非持倉 -> summary/evidence/report short last group；CHANGELOG 描述與 scoped diff 基本一致。
  - 測試 fixture 同時含持倉 智原 與未持倉 建準，驗證 智原/續抱 只在 messages[0]，建準 只在 messages[1]，summary/evidence 在 messages[2]。
  - 策略 / 顯示語意未因排序改變：測試保留持倉 action、未持倉狀態、fail-closed、market theme evidence 等既有斷言；本輪 diff 未改 strategy engine。
  - 質疑點：`include_detail=True` 時 Details Backup 會追加在 summary/evidence 後方。實際 `generateReport()` 呼叫未傳 `include_detail=True`，預設為 false；因此 Owner 手機主要 delivery path 仍是三則訊息，summary/evidence 為最後一則。此點列為旁支風險，不阻塞本輪。

  ## 使用者誤讀風險

  - 手機端第一則已變成持倉、第二則未持倉，降低先看到 summary 而誤以為已有可執行推薦的風險。
  - summary/evidence 合併為第三則，仍保留「新倉：無有效進場」、production source insufficient 等 fail-closed 文案；未看到用假 evidence 補過測試。
  - 非阻塞殘留：若未來啟用 `include_detail=True` 送 live Telegram，Details Backup 會在 summary/evidence 後方，可能讓「最後一則」語意變成 debug backup；建議另開任務定義 detail delivery contract。

  ## 質疑與反證

  - 主動反證 1：不只重跑 Tech 自檢，補跑直接 consumer mock：`send_many(["【持倉標的】...", "【未持倉標的】...", "summary/evidence"], reply_markup=...)`。結果確認 sender 保留 list order，reply markup 只掛最後一則。
  - 主動反證 2：第一次未指定 `arch -arm64` 跑 pytest 時遇到 `pydantic_core` native wheel 架構錯誤；改用 Tech 同口徑 `arch -arm64` 後測試正常，環境問題未被當作豁免。
  - 執行測試：
    - `arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py tests/test_market_theme_evidence.py`：115 passed，165 warnings。
    - `arch -arm64 .venv/bin/python -m pytest -q tests/test_notifier.py`：3 passed。

  ## 未測項目

  - 未做 live Telegram delivery。
  - 未做 production DB write / schema / RLS / grant / policy / role / index / constraint 驗證；本輪 diff 不涉及。
  - 未做 full pytest、replay、backfill、全 evidence 矩陣；依 tiny_patch / L1 風險預算停止。
  - 未驗證 Telegram reply markup 在新 order 下的產品落點；CHANGELOG 已列旁支待辦。

  ## QA 結論

  通過
