# QA_REPORT: Phase 0 + B1-B5 前置修復與手機閱讀回歸

  ## 測試範圍

  - 讀取並比對 TASK.md、CHANGELOG.md、git diff。本輪可吸收 diff：CHANGELOG.md、core/generator.py、presentation/report.py、tests/test_generator_report.py。
  - worktree 殘留：同上 4 個 tracked modified，未看到無關 tracked diff；QA 未修改 tracked file。
  - 任務尺寸為 risk_patch、QA level L3；驗證聚焦 Telegram formatter / message list / funnel count / 持倉排序，未擴成 full pytest、replay、backfill 或 production matrix。

  ## 風險預算與停止條件

  本輪最值得抓的風險：

  1. Phase0 缺來源仍顯示強證據或正向行動語意。驗證：score gate tests + QA alias probe。停止條件：出現 證據不足｜S5/5、S 5/5、極強 或 insufficient/missing 仍支持行動。
  2. B1/B2 手機卡片語意自撞。驗證：持倉 / 未持倉 card 與完整 message list 禁用字串掃描。停止條件：出現 條件：觀察：觀察天數未確認、弱勢｜極強、遠離突破｜極強。
  3. B3/B4/B5 跨區塊 count / 排序不一致。驗證：summary、風控區、詳情索引、未持倉卡片同份 message list 交叉比對。停止條件：六檔少列、排序不一致、隔日確認 併入 等冷卻 或 funnel/card count 不一致。

  ## 關聯風險掃描

  - CHANGELOG.md 已同步本輪 Phase 0 + B1-B5，與 TASK.md 主目標一致；不再是 stale 的上一輪六檔持倉任務。
  - core/generator.py 版本由 v20.4.28 升為 v20.4.29，符合不得回退版本契約。
  - presentation/report.py 的 score gate 只允許 available / derived 顯示 S 分數，insufficient / missing alias 走 S 證據不足。
  - B5 新增 隔日確認 bucket，summary / execution checklist / funnel formatter 均有同步；未發現 DB schema、write path、live Telegram delivery 或策略核心公式變更。
  - 清理 / 瘦身 / refactor 證據表要求不適用，本輪不是清理任務。

  ## 跨區塊語意一致性

  - Tech 自檢重跑：tests/test_generator_report.py 119 passed，225 warnings；warnings 為既有依賴 deprecation 類。
  - py_compile core/generator.py presentation/report.py tests/test_generator_report.py passed。
  - git diff --check passed。
  - QA 額外手機閱讀 probe passed：
      - message order：持倉、未持倉、summary。
      - 六檔持倉排序一致：英業達,緯創,技嘉,南亞科,智原,建準，summary 風控區與詳情索引一致。
      - funnel line：可買 0｜不可追高觀察 0（不可買）｜隔日確認 1｜僅追蹤 0｜淘汰 0。
      - 隔日確認 1 檔，不列入交易執行 存在，等冷卻 1 不存在。
  - 注意：仍支持 仍可出現在市場 / 題材背景 available 的趨勢敘述；本輪禁止的是 insufficient / missing 狀態仍支持行動，未在驗證輸出中發現違反。

  ## 使用者誤讀風險

  - Phase0：缺 score source 不再讓手機讀者看到 S 5/5 或 極強，降低「資料不足但看似滿分」誤讀。
  - B1：弱勢觀察缺天數時，條件行為 條件：觀察天數未確認...，未見 觀察：觀察 雙詞。
  - B2：弱勢 / 遠離突破時，強度降為 待確認，未見 弱勢｜極強 或 遠離突破｜極強。
  - B5：隔日確認獨立呈現且標明不列入交易執行，手機閱讀不會被等冷卻 count 混淆。

  ## 質疑與反證

  - 反證 Tech 未完全覆蓋的路徑：QA 自建混合 message list，同時包含六檔持倉與一檔隔日確認未持倉，直接檢查前三則手機報文整體，而非只測單一 helper。
  - 另補 Phase0 alias 反證：source_status=insufficient / missing 直接渲染持倉 card，確認顯示 S 證據不足 且不顯示 S 5/5 / 極強。
  - 另補 B2 持倉 card 反證：score available 但盤面弱勢 + 遠離突破時，顯示 盤面：弱勢｜待確認，未出現極強矛盾。

  ## 未測項目

  - 未跑 full repo pytest；本輪 TASK 明確是 formatter / message list / funnel / 排序風險，已跑相關完整測試檔與 QA 額外 probe。
  - 未做 production read smoke、DB write、backfill、live Telegram delivery；均屬本輪非目標或禁止事項。
  - 未驗證 evidence_score / final_confidence / decision_eligible major 改造，依 TASK 屬旁支待辦。

  ## QA 結論

  通過
