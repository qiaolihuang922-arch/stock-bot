# TASK: May Data Strategy Report Full Integrity Check

## 任務狀態

- task_id: may-data-strategy-report-full-integrity-check
- 任務類型: risk_patch
- 任務尺寸判斷: risk_patch
- 狀態: ready_for_tech
- 版本建議: patch
- 版本契約:
- 本輪主要是 integrity check / dry-run / smoke verification，預設不改使用者可見 Telegram/report 文案與 header，沿用目前 Telegram header v20.4.6。
- 若 Tech 發現必須修改策略 decision、summary、card、checklist、funnel、formatter header 或 message list contract 才能修復衝突，必須停止並回報 PM/Architect 另開修復任務；不得在本輪順手改使用者可見契約。
- QA 分級建議: L3
- QA 升級原因: 本輪驗證 production DB source-of-truth、GitHub/fresh runner dry-run、策略與顯示一致性、手機長報文跨區塊一致性，必須包含 fresh-run/local-context-cleared 反證與 production read-only smoke。

## Owner 問題

五月資料已完成寫入後，Owner 需要確認正式系統不是只在本機、runtime、fake fixture、daily_signal_snapshot 或舊 script report 裡「看起來能跑」，而是：

- 策略 decision 確實能從 production DB / 五月資料取得必要 market/theme evidence。
- git / fresh runner 在 dry-run 條件下能產生 Telegram/report 報文。
- 策略 decision 與顯示層 summary / card / checklist / funnel 沒有互相矛盾。
- 報文本身跨區塊的數量、分類、行動、版本、已執行 / 待執行沒有衝突。

本輪價值是建立完整 integrity check 矩陣與最小驗證閉環；不是重設策略、補歷史資料、改 schema、live Telegram 或新增假資料。

## 使用者可見結果

Owner / Architect 會從 CHANGELOG.md 與 QA_REPORT.md 看到一份明確結論：

- production DB / 五月資料是否被正式策略與報文路徑消費。
- fresh runner / local context cleared 後是否仍能 dry-run 產生報文。
- 報文是否存在跨區塊 decision、分類、數量、行動或版本衝突。
- 若 blocked，明確指出阻塞類型：缺 production read env、缺 production rows、DB schema / permission 不足、runner path 無法重建、報文契約衝突、或需要另開修復任務。

本輪不發 live Telegram；手機閱讀檢查使用 dry-run / sample report / fixture output。

## 非目標

- 不 live Telegram。
- 不改 DB schema、table、column、RLS、grant、policy、role。
- 不新增假資料、synthetic rows、fixture rows 到 production。
- 不直接手寫 production DML。
- 不新增五月 market/theme historical source。
- 不回填或重寫五月資料。
- 不把 daily_signal_snapshot、local cache、runtime dict、worktree 暫存、舊報文文字或 backfill script output 冒充 market/theme evidence source-of-truth。
- 不改策略買賣門檻、RR、停損停利、持倉狀態機、watchlist。
- 不重構 formatter、runner、DB layer。
- 不修所有旁支 bug；若發現不阻塞本輪 integrity conclusion 的問題，只列 follow-up。

## 影響模組

- 直接模組:
- production DB read-only smoke / source audit。
- GitHub runner 或等價 fresh-run dry-run entrypoint。
- 正式 Telegram/report generation path。
- strategy decision 與 market/theme evidence consumption path。
- summary / card / checklist / funnel formatter contract。
- 相關 smoke tests、fixtures、diagnostic JSON output。
- 直接消費者:
- Owner：判斷五月資料寫入後正式報文是否可信。
- Architect：依 CHANGELOG.md / QA_REPORT.md 收口是否可進下一輪。
- QA：依本任務矩陣做 fresh-run、production read-only、手機長報文反證。
- Telegram/report reader：只消費 dry-run/sample output，不接收 live message。

## 輸出契約

本輪需要 Tech 交付一個 integrity verification summary，可由既有 diagnostic script、測試輸出或 CHANGELOG.md 摘要呈現；不得要求 Owner 手動讀 DB 才能判斷。

必要 JSON / dict 形狀：

{
"mode": "may-data-strategy-report-full-integrity-check",
"schema_change": false,
"data_write": false,
"live_telegram": false,
"telegram_header_version": "v20.4.6",
"source_integrity": {
"production_db_readonly": "passed|failed|blocked",
"may_data_available": "passed|failed|blocked",
"market_theme_source_of_truth": "production.market_theme_confirmed_evidence|blocked",
"uses_fake_or_local_as_market_theme_evidence": false,
"uses_daily_signal_snapshot_as_market_theme_evidence": false
},
"fresh_runner_dry_run": {
"local_context_cleared": true,
"report_generated": "passed|failed|blocked",
"live_telegram_disabled": true
},
"decision_display_consistency": {
"strategy_vs_summary": "passed|failed|blocked",
"strategy_vs_cards": "passed|failed|blocked",
"strategy_vs_checklist": "passed|failed|blocked",
"strategy_vs_funnel": "passed|failed|blocked"
},
"report_cross_section_consistency": {
"counts": "passed|failed|blocked",
"categories": "passed|failed|blocked",
"actions": "passed|failed|blocked",
"executed_vs_pending": "passed|failed|blocked",
"version": "passed|failed|blocked"
},
"blocked_reasons": [],
"followups": []
}

已存在且不得回退的契約：

- 最新使用者可見 Telegram 版本為 v20.4.6。
- market_theme_confirmed_evidence 是 market/theme trend consumption 的 production source-of-truth。
- daily_price / daily_signal_snapshot 不得被包裝成 market/theme evidence。
- local/runtime/cache/worktree/chat/report-derived payload 不得作為跨日記憶或 production evidence。
- fresh runner 必須可由 production DB 或 Owner-approved persistent source 重建判斷。
- 缺 DB env、缺 rows、權限不足、資料不足時必須 fail closed：missing-source / source-error / insufficient-data / blocked。
- live Telegram 不在本輪。
- DB schema / RLS / grant / policy / role 變更必須停下找 Owner。
- 非 schema 資料檢查與 dry-run 不找 Owner。

## 驗收條件

1. Source integrity

- Tech 必須提供 production read-only smoke 或等價驗證，確認策略與 production DB / 五月資料有實際關聯。
- 驗證必須明確排除 fake、local、runtime、worktree cache、report-derived payload。
- 驗證必須明確排除把 daily_signal_snapshot 冒充 market/theme evidence。
- 若 production DB 讀取失敗或資料不足，結果必須 blocked / fail closed，不得補 fallback。

2. Fresh runner dry-run

- Tech 必須提供 git/fresh runner 等價 dry-run 入口或 smoke，證明清空 local context 後仍能產生 Telegram/report sample。
- dry-run 必須禁用 live Telegram。
- 若正式 runner 依賴本機對話、runtime dict、未提交檔案或 worktree 暫存才能成功，QA 必須 blocked。

3. Decision vs display

- 必須檢查 strategy decision 與 summary、card、checklist、funnel 的主行動一致。
- 同一檔不可在不同區塊同時出現可買 / 不可買、加碼 / 減碼、已執行 / 待執行等相反語意。
- 若發現衝突，本輪可記錄為 failed / blocked；不得順手改使用者可見報文契約。

4. Report cross-section consistency

- 必須檢查 dry-run 長報文中的跨區塊數量、分類、行動、版本、已執行 / 待執行一致。
- 手機閱讀順序必須以 Owner 打開 Telegram 後先看到的 summary / 決策區開始檢查，再追到 cards / checklist / funnel / details。
- 空區塊、0-count、同義重複行動、不同分類混成同一行，均需列入手機噪音與誤讀風險檢查。

5. QA 必做反證

- fresh-run / local-context-cleared 反證。
- production read-only smoke。
- 手機長報文一致性檢查。
- 至少一個負面案例：production source 不足或 forbidden source 出現時，系統必須 fail closed，而不是產生 confirmed evidence 或正常買賣結論。

## 範例或 fixture

手機閱讀路徑：

1. 先看 Telegram header：版本應為 v20.4.6，且 dry-run 不 live send。
2. 先看最後 summary / 今日結論：是否清楚區分可買、僅追蹤、不可行動。
3. 再看持倉與未持倉 cards：主行動是否與 summary 一致。
4. 再看 checklist / funnel：數量、分類、待執行與已執行是否能對回 cards。
5. 最後看 details：只追溯原因，不得反轉前面主行動。

成功範例形狀：

Header: 台股策略報告 v20.4.6 dry-run

今日結論
- 新倉：無有效進場
- 持倉：先風控，不加碼
- 僅追蹤：2 檔見詳情
- 不可行動：量能不足 3、等冷卻 1

持倉卡
- 2330：主行動=續抱觀察；不加碼；原因=風控優先

未持倉卡
- 2317：僅追蹤；不可買；原因=等冷卻

Funnel
- 可買 0
- 僅追蹤 2
- 不可行動 4

Blocked 範例形狀：

Header: 台股策略報告 v20.4.6 dry-run

今日結論
- 新倉：2317 可買

未持倉卡
- 2317：不可買；原因=等冷卻

Funnel
- 可買 1
- 等冷卻 1

Blocked reason:
- summary says BUY but card says cooldown/not-buyable for the same symbol

Integrity JSON 成功範例：

{
"mode": "may-data-strategy-report-full-integrity-check",
"schema_change": false,
"data_write": false,
"live_telegram": false,
"telegram_header_version": "v20.4.6",
"source_integrity": {
"production_db_readonly": "passed",
"may_data_available": "passed",
"market_theme_source_of_truth": "production.market_theme_confirmed_evidence",
"uses_fake_or_local_as_market_theme_evidence": false,
"uses_daily_signal_snapshot_as_market_theme_evidence": false
},
"fresh_runner_dry_run": {
"local_context_cleared": true,
"report_generated": "passed",
"live_telegram_disabled": true
},
"decision_display_consistency": {
"strategy_vs_summary": "passed",
"strategy_vs_cards": "passed",
"strategy_vs_checklist": "passed",
"strategy_vs_funnel": "passed"
},
"report_cross_section_consistency": {
"counts": "passed",
"categories": "passed",
"actions": "passed",
"executed_vs_pending": "passed",
"version": "passed"
},
"blocked_reasons": [],
"followups": []
}

## 明確禁止事項

- 禁止 live Telegram。
- 禁止 DB schema / table / column / RLS / grant / policy / role 變更。
- 禁止 production write / backfill / data mutation。
- 禁止新增 fake / synthetic / fixture rows 到 production。
- 禁止直接手寫 production DML。
- 禁止把 local/runtime/cache/worktree/chat/report-derived payload 當 production source。
- 禁止把 daily_signal_snapshot 冒充 market/theme evidence。
- 禁止為了通過驗收放寬買點、RR、風控、停損停利或持倉規則。
- 禁止在本輪修改 Telegram 使用者可見契約；發現需修復時 blocked 並列 follow-up。
- 禁止擴成全量重構、全量清理、策略重設或歷史資料補齊任務。

## 阻塞條件

- 需要 DB schema / table / column / RLS / grant / policy / role 變更。
- production read-only env / permission 不足，且無法用 approved persistent mocked DB rows 做等價 fresh-run 反證。
- 五月資料缺失到無法判斷 strategy/report integrity。
- 正式 runner dry-run 無法在 live Telegram disabled 條件下產生 sample report。
- report 必須修改使用者可見契約才能消除衝突。
- 發現策略 decision 與 summary/card/checklist/funnel 有相反行動。
- 發現報文跨區塊數量、分類、行動、版本、已執行 / 待執行無法對齊。
- TASK / CHANGELOG / QA_REPORT 任一交付無法列出證據與反證。

## 本輪停止條件

- 已完成 production read-only source integrity check。
- 已完成 fresh-run / local-context-cleared dry-run report generation check。
- 已完成 strategy decision vs summary/card/checklist/funnel 一致性檢查。
- 已完成手機長報文跨區塊 counts/categories/actions/version/executed-vs-pending 一致性檢查。
- 已證明本輪無 schema change、無 production write、無 live Telegram、無假資料。
- 旁支問題只列入 followups，不納入本輪修復，除非它直接阻塞上述 integrity conclusion。
