# QA_REPORT:

  ## 測試範圍

  本輪 QA 風險預算：normal_patch / L2，停止於 official formatTelegramMessages message-list replay，不擴成 full pytest / production DB / live Telegram。

  已讀取並比對：

  - TASK.md
  - CHANGELOG.md
  - git diff
  - core/generator.py
  - presentation/report.py
  - tests/test_generator_report.py

  可吸收 diff：

  - core/generator.py：VERSION v20.4.44
  - presentation/report.py：Telegram card wording / evidence rendering
  - tests/test_generator_report.py：focused official message-list regressions
  - CHANGELOG.md：本輪 Tech 摘要

  worktree 殘留：

  - git status --short 只顯示上述 4 個 modified tracked files。
  - QA 未修改 tracked file；.qa_tmp/ 暫存未出現在 git status。

  執行命令：

  - Tech focused slice：4 passed
  - v20.4.42 / v20.4.43 regression slice：14 passed
  - QA-only inline mobile replay：passed
  - py_compile core/generator.py presentation/report.py tests/test_generator_report.py：passed after PYTHONPYCACHEPREFIX=.qa_tmp/pycache
  - git diff --check：passed

  第一次 pytest / py_compile 曾因環境寫入或架構問題失敗：pytest 用預設 x86_64 撞到 arm64 pydantic_core，py_compile 嘗試寫入 ~/Library/Caches 被 sandbox 擋下；改用 arch -arm64 與 .qa_tmp 後通過，不列為產品阻塞。

  ## 風險預算與停止條件

  最值得抓的風險：

  1. 手機卡片仍外露 generic/internal wording：決策證據：來源可追溯、hard stop、持倉硬風控、既有買點與倉位規則通過。
     驗證：official message-list replay 與 QA-only mobile replay 全文反查。
     停止條件：任一 raw/internal 詞出現在 Owner 可讀卡片即阻塞。
  2. 光寶科 prepare 被誤讀成可下單或買點已通過。
     驗證：盤後 official unheld card 必須顯示 明日準備｜不可下單、開盤確認未完成、盤後待開盤確認、明日開盤後仍守突破區 / 不追價。
     停止條件：出現可下單語意或 既有買點與倉位規則通過 即阻塞。
  3. 持倉 hard stop / reduce 只剩 raw gate 或無數字距離。
     驗證：QA-only replay 補測硬風控減碼卡，確認顯示 距警戒線 2.04%，距停損線 1.05%，結構轉弱，且不顯示 raw hard-stop wording。
     停止條件：減碼 / 停損卡缺人話原因或可用距離即阻塞。

  ## 關聯風險掃描

  TASK.md、CHANGELOG.md、diff 一致：本輪是 Telegram formatter wording / version / focused tests，未看到策略 decision、RR formula、DB schema/write、live Telegram diff。

  v20.4.43 hard-gate fail-closed 未回退：missing/source-error/conflict focused cases 仍 blocked，summary 不升格新倉建議；v20.4.42 卡關主因 / 量化差距 readability regression 仍通過。

  掃描到 raw 詞仍存在於內部 payload / generator decision_judgment / 舊測試 fixture，例如 core/generator.py 內部 blocking reason 與舊測試 note。這些不是本輪阻塞，因 TASK 禁的是使用者可見 Telegram card 外露；official
  rendered output 已反證未外露於本輪覆蓋路徑。

  ## 跨區塊語意一致性

  按手機閱讀順序檢查 position -> unheld -> summary：

  - Summary header/version 為 v20.4.44。
  - 光寶科 unheld prepare card：標題仍是 明日準備｜不可買｜開盤後確認，買點行是 明日準備｜不可下單，未與 summary 的不可下單語意衝突。
  - 華邦電 / 技嘉 overheat、旺宏 failed breakout：卡關主因與量化差距一致，且 primary blocker 沒被 RR / entry quality 搶焦點。
  - 建準 holding observation：沒有 generic 決策證據：來源可追溯 或硬風險 evidence 行。
  - 硬風控減碼：position card 的主行動、原因、距警戒/停損數字一致，沒有 raw hard stop 外露。

  ## 使用者誤讀風險

  已反證主要手機誤讀路徑：

  - Prepare 不會被讀成可下單：明日準備｜不可下單 + 開盤確認未完成 + 盤後待開盤確認。
  - Generic evidence 不再像交易依據：rendered output 未出現 決策證據：來源可追溯。
  - Holding observation 不會被刷成新倉 evidence：建準續抱觀察卡只保留持倉決策與風控條件。
  - Reduce/stop 不再用 raw gate 命名：QA-only 減碼卡顯示人話與數字距離。

  殘留可讀性風險：部分既有持倉 note 仍可能在舊 fixture 中含 raw 字樣，若未來那些舊路徑被納入 v20.4.44 使用者可見 specimen，需另開 focused wording 任務。本輪 official covered path 未外露。

  ## 質疑與反證

  主動質疑 1：Tech 測了停損，但 Owner 也要求 hard stop / reduce holding card。
  反證：QA-only replay 建立 華邦電 硬風控減碼卡，確認 風險依據：距警戒線 2.04%，距停損線 1.05%，結構轉弱，且無 hard stop / 持倉硬風控。

  主動質疑 2：建準 holding observation 是否仍會顯示 generic evidence。
  反證：QA-only replay 建立 建準 續抱觀察卡，確認無 決策證據：來源可追溯、無 風險依據：卡關。

  主動質疑 3：prepare basis 會不會蓋過不可下單語意。
  反證：光寶科卡片先顯示 買點：明日準備｜不可下單、卡關主因：開盤確認未完成、量化差距：盤後待開盤確認、解鎖：明日開盤後仍守突破區 / 不追價，RR / 量能 / 回測只在 依據，未搶主 gate。

  ## 未測項目

  - 未跑 full pytest，符合 normal_patch / L2 風險預算。
  - 未跑 production runner artifact。
  - 未讀 production DB source artifact。
  - 未做 DB write/backfill/manual DML。
  - 未做 live Telegram delivery。
  - 未驗全市場所有卡片 wording 矩陣。

  ## QA 結論

  通過
