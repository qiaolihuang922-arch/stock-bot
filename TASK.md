# TASK: 拆分純 Telegram 顯示 helper 到 presentation

## 任務狀態

- task_id: pm-20260601-telegram-helper-split
- 任務類型: normal_patch
- 狀態: qa_passed
- 版本建議: 不升版，不修改 VERSION
- QA 分級建議: L2
- 本輪主 bug: 上一輪 PM 契約誤把 Tech worktree 的 detached HEAD / git completion gate 納入 Tech blocked 條件；本輪修正為 git completion gate 只由 Architect 在主 repo 收口執行。

## Owner 問題

core/generator.py 內仍混有一組純 Telegram 顯示 helper，需小步拆分到 presentation/report.py 或 presentation 內既有文件，降低 generator 的顯示責任；同時不得把任務擴大成策略、DB、狀態機或架構重做。

## 使用者可見結果

Telegram 報文內容、順序、文案、版本字串、策略判斷與資料語意不可改變。使用者在手機上看到的報文應與拆分前一致，只是內部 helper 所在模組改為 presentation 層。

手機閱讀路徑：

- GitHub runner / dry-run 產出的 Telegram report message list
- Owner 手機 Telegram 內看到的 summary、持倉卡、未持倉卡、brief data evidence 區塊
- 本輪不得 live delivery，只驗 dry-run / 測試 fixture 的輸出形狀與內容一致性

Telegram 多訊息順序沿用既有契約，不要求改文案：

1. 持倉卡
2. 未持倉卡
3. brief data evidence / summary 短訊
4. Details Backup 僅在 include_detail=True 時追加最後

單一 message 內的 summary、持倉卡、未持倉卡、brief data evidence 文案與欄位不可因搬移而改變。

## 非目標

- 不改 strategy decision、RR、holding_status、買賣 / 加減碼 / 停損停利判斷。
- 不改 DB read/write、DB schema、RLS、grant、policy、role、index / constraint。
- 不改 Telegram 文案、分組語意、排序、空區塊顯示規則或 VERSION。
- 不新增新的業務模組，不新增架構文檔。
- 不清理 unrelated helper，不做全量 presentation 重構。
- 不修復測試中暴露的旁支產品問題，除非直接阻塞本輪 helper 搬移；旁支只記 follow-up。

## 影響模組

允許影響：

- core/generator.py
- presentation/report.py
- presentation 內既有純顯示文件
- 對應既有測試或 import boundary gate 測試

優先搬移 helper：

- formatTelegramPositionCard
- formatTelegramUnheldCard
- formatTelegramSummary
- format_brief_data_evidence_message
- 上述 helper 的直接純顯示依賴

不得牽動：

- DB writer / signal writer / strategy evidence writer
- strategy / validator / holding status / position store 的業務決策邏輯
- result mutation、results_map mutation、holding_decision mutation
- core/services 新增 presentation import

## 直接消費者

- core/generator.py 產生 Telegram report 的既有流程
- Telegram message list / report rendering tests
- import boundary gate
- Owner 手機閱讀 Telegram 報文的 summary、持倉卡、未持倉卡與 evidence 區塊

## 輸出契約

### 模組契約

- 純 Telegram 顯示 helper 搬到 presentation/report.py 或 presentation 內既有文件。
- core/generator.py 可作為 transitional bridge import presentation helper。
- core/services 不得新增任何 presentation import。
- presentation 不得 import DB writer、signal writer、strategy evidence writer。
- presentation helper 不得直接 mutate results_map、result、holding_decision。

### 報文契約

- Telegram message list 內容不變。
- Summary、position card、unheld card、brief data evidence 的可見文案不變。
- 分組、排序、狀態標籤、漏斗語意不變。
- 空區塊 / 0-count / 無新增下單占位規則不變。
- VERSION 不變。

### Git / runner 契約

- Tech 不執行也不以 git completion gate 作為 blocked 條件。
- Tech worktree 若為 detached HEAD，不得因此 blocked。
- git completion gate 僅由 Architect 在主 repo 收口執行。

## 已存在且不得回退的契約

- core/generator.py 仍是既有 Telegram report orchestration 的直接消費者入口。
- presentation 層不得依賴 DB writer、signal writer、strategy evidence writer。
- core/services 不得新增 presentation import。
- 不得改變任何策略輸出、RR、holding_status、DB read/write 或 Telegram 可見文案。
- 若現有 import boundary gate 已覆蓋上述規則，必須保留並確認仍會抓違規。
- 若某 helper 的直接依賴不是純顯示，而會牽動策略、DB、holding_status 或 result mutation，本輪不得硬搬，必須縮小範圍或 blocked。

## 驗收條件

1. Helper 搬移完成後，Telegram 相關輸出與搬移前一致；至少覆蓋 summary、持倉卡、未持倉卡、brief data evidence 的既有 fixture / snapshot / 等價斷言。
2. import boundary gate 仍能阻止 presentation import DB writer / signal writer / strategy evidence writer，並阻止 core/services 新增 presentation import。
3. presentation helper 不直接 mutate results_map、result、holding_decision。
4. 必跑完整邏輯測試並記錄結果：
- tests/test_generator_report.py
- tests/test_market_theme_evidence.py
- tests/test_analysis_engine.py
- tests/test_strategy_evidence.py
- tests/test_position_store.py
- tests/test_cross_day_context.py
- tests/test_signal_validator.py
5. 如時間可接受，追加：
- tests/test_daily_snapshot_store.py
- tests/test_dry_run_replay.py
6. QA 需額外反證：
- 輸出未改變。
- import gate 仍抓違規。
- 完整邏輯測試通過，或因明確環境 / 依賴問題 blocked。
- Tech 沒有把 detached HEAD / git completion gate 當 blocked 條件。

## 範例或 fixture

使用既有 Telegram report 測試 fixture，不新增產品文案。

最小驗收案例：

case A: 有持倉 + 有未持倉追蹤
expect:
- summary 文案不變
- position card 文案、順序、主行動不變
- unheld card 文案、狀態不變
- brief data evidence 文案不變

case B: import boundary negative case
expect:
- presentation -> DB writer / signal writer / strategy evidence writer 依賴被 gate 擋下
- core/services -> presentation 依賴被 gate 擋下

## 明確禁止事項

- 禁止 DB write。
- 禁止 live Telegram delivery。
- 禁止修改 VERSION。
- 禁止修改 Telegram 文案。
- 禁止修改策略 decision、RR、holding_status、DB read/write。
- 禁止新增新的業務模組或架構文檔。
- 禁止把 pure display helper 搬移擴大成 generator 全量重構。
- 禁止 presentation 直接 mutate results_map、result、holding_decision。
- 禁止 presentation import DB writer / signal writer / strategy evidence writer。
- 禁止 core/services 新增 presentation import。
- 禁止 Tech 因 detached HEAD 或 git completion gate blocked；該 gate 只由 Architect 在主 repo 收口。

## 阻塞條件

- 目標 helper 的直接依賴必須搬入策略 / DB / holding_status / result mutation 才能運作，且無法只搬純顯示部分。
- 既有測試或 fixture 不足以證明 Telegram 輸出未變，且無法在本輪建立等價輸出驗證。
- import boundary gate 不存在或不可執行，且無法用本輪測試補足。
- 測試環境缺依賴且無法補齊，需列出實際錯誤，不得宣告通過。
- 發現搬移會要求 DB schema / live delivery / production write，立即 blocked。

## 本輪停止條件

完成到以下範圍即停止：

- 優先 helper 與其純顯示直接依賴已搬到 presentation 既有文件。
- core/generator.py 只保留必要 transitional bridge / orchestration。
- Telegram 輸出等價驗證通過。
- import boundary gate 驗證通過。
- 指定完整邏輯測試通過，或清楚 blocked。

以下旁支不納入本輪：

- 其他 generator helper 清理。
- 報文文案優化。
- 策略判斷修正。
- DB / replay / backfill 流程改善。
- 全量 presentation 架構整理。
- git completion gate 的 runner 實作修改；本輪只修正 Tech 任務契約，不要求 Tech 跑 gate。
