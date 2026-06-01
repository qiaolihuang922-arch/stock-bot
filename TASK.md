# TASK: 保守拆分 Telegram 顯示層到 presentation/report module

## 任務狀態

- task_id: pm-20260601-presentation-report-split
- 任務類型: normal_patch
- 狀態: qa_conditional_pass_pending_git_stage
- 版本建議: v20.4.21
- QA 分級建議: L2
- 主問題: 第一刀保守拆分顯示層，不重設策略、不擴大清理範圍。

## Owner 問題

Owner 要求拆分策略層與顯示層：策略 decision 邏輯不要混入 Telegram 使用者可見報文格式化。本輪只做第一刀，從 core/generator.py 抽出 Telegram 顯示層到獨立 presentation/report 類 module；策略、DB、evidence、holding 狀態機
不改。

## 使用者可見結果

- Telegram 報文內容、順序、手機閱讀體驗維持既有結果。
- 使用者仍透過既有 public entry 使用 formatTelegramMessages，或透過明確 import bridge 相容。
- 報文 header / version 顯示更新到 v20.4.21，不得回退既有可見版本契約。
- 無有效進場時，手機上不得出現像推薦的「最強標的」區塊或文案。

## 非目標

- 不改策略 decision。
- 不改 RR 計算。
- 不改 holding_status 判斷。
- 不改 record_daily_signals。
- 不改 record_strategy_evidence。
- 不改 Supabase / DB read-write path。
- 不改 production DB schema、RLS、grant、policy、role、index、constraint。
- 不做全量 generator 重構。
- 不拆多個無關檔案。
- 不新增 live Telegram delivery。
- 不新增或改寫跨日持久化 source-of-truth。

## 影響模組

- 主要影響:
- core/generator.py
- 新增或調整一個獨立 Telegram presentation/report module，例如 presentation/report.py 或既有同等命名位置。
- 對應測試 / gate。
- 不應影響:
- 策略 decision module。
- RR module。
- holding 狀態機。
- DB client / Supabase service。
- evidence recording。
- daily signal recording。
- live delivery runner。

## 直接消費者

- Telegram 報文產生流程。
- 既有呼叫 formatTelegramMessages 的 runner / CLI / tests。
- Owner 手機閱讀 Telegram messages 的最終輸出。

## 輸出契約

### Public import contract

- 必須保留 formatTelegramMessages public compatibility。
- 若實作搬移到新 module，core/generator.py 必須提供明確 import bridge 或相容 wrapper。
- 既有 consumer 不應因 import path 改變而破壞。

### Presentation input contract

- 新 presentation/report module 只能讀取已生成的 results_map / report_context 或既有等價格式化上下文。
- 顯示層不得直接取得 DB client。
- 顯示層不得呼叫 record / write / evidence side effect。
- 顯示層不得 mutate result、holding_decision 或 strategy output object。

### Telegram message contract

- 輸出仍為三則 Telegram messages，與既有關鍵 fixture 的內容、分組、順序保持一致，除版本字串升到 v20.4.21 外不得任意改文案。
- 手機閱讀路徑維持既有 Owner 指定順序:
- 第 1 則: 持倉標的 / 持倉先處理什麼。
- 第 2 則: 未持倉標的 / 可準備、僅追蹤、淘汰。
- 第 3 則: 簡報＋資料依據 / 今日能不能買、風險、補充證據。
- 無有效進場時:
- Summary 應呈現「新倉：無有效進場」或既有等價不可買文案。
- 不得顯示「最強標的」作為可買推薦。
- 不得出現會讓手機使用者誤讀為可下單的標題、排序或 CTA。

### 已存在且不得回退的契約

- formatTelegramMessages 可被既有 caller import / call。
- 三則 messages 的主要輸出形狀維持。
- 既有關鍵 fixture 對應的 Telegram 輸出維持。
- 無有效進場不顯示最強標的。
- maturity gate 仍為 100。
- 策略 decision、RR、holding_status、record_daily_signals、record_strategy_evidence、DB read/write path 行為不變。
- 若 Tech 無法在現有 repo 中確認上述既有 fixture 或 caller，必須 blocked，請 Architect 補 fixture / caller 名稱，不得自行假設新契約。

## 驗收條件

1. 結構拆分
- Telegram 使用者可見 formatting / message assembly 已從 core/generator.py 抽到獨立 presentation/report module。
- core/generator.py 僅保留相容入口、資料準備或 orchestration 所需最小 glue。
2. Side-effect gate
- 新 presentation/report module 不 import:
- record_daily_signals
- record_strategy_evidence
- get_supabase_client
- 新 presentation/report module 不呼叫 DB write 或 evidence write。
- 顯示層不 mutate result / holding_decision，需用測試、lint gate、AST 檢查或等價可重跑命令證明。
3. Output regression
- 既有關鍵 fixture 產生的三則 Telegram messages 與拆分前一致。
- 允許差異僅限版本字串更新為 v20.4.21，若現有版本契約另有常量，必須同步更新。
- 無有效進場 fixture 不顯示最強標的。
- maturity gate 驗證仍為 100。
4. Compatibility
- 既有 formatTelegramMessages import path 仍可用，或有明確 bridge 測試覆蓋。
- 直接 consumer 測試至少覆蓋一條現有 runner / formatter call path。

## 範例或 fixture

Tech 必須使用 repo 內已存在的關鍵 fixture；若 fixture 名稱不明，先用 rg 找既有 Telegram formatter / generator snapshot / expected message 測試。

最低 fixture 組合:

- fixture_existing_three_messages: 既有正常報文案例，驗證輸出仍為 3 則 messages。
- fixture_no_valid_entry: 無有效進場案例，驗證不顯示最強標的，Summary 只呈現不可買。
- fixture_maturity_gate: 驗證 maturity gate 仍為 100。

示例輸出形狀，不要求逐字新增:

Message[0]
v20.4.21
持倉標的
持倉：...

Message[1]
未持倉標的
可準備 / 僅追蹤 / 淘汰...
不得出現「最強標的」作為可買推薦

Message[2]
簡報＋資料依據
新倉：無有效進場 / 風控 / 補充證據...

## 明確禁止事項

- 禁止修改策略 decision 結果。
- 禁止修改 RR、maturity gate、holding_status。
- 禁止在 presentation/report module import 或呼叫 DB client。
- 禁止在 presentation/report module record strategy evidence。
- 禁止在 presentation/report module write DB。
- 禁止顯示層 mutate input objects。
- 禁止把本輪擴成全量 architecture rewrite。
- 禁止清理無關 legacy code。
- 禁止 live Telegram delivery。
- 禁止 production DML 或 DB schema 變更。
- 禁止用「測試通過」宣告策略正確；本輪只驗顯示層拆分與輸出未回退。

## 阻塞條件

- 找不到既有 formatTelegramMessages consumer，且無法確認 public compatibility 需求。
- 找不到可代表現有三則 messages 的 fixture / snapshot / expected output。
- 找不到 maturity gate 既有契約來源，無法證明仍為 100。
- 拆分必須修改策略 decision、RR、holding_status 或 DB write path 才能完成。
- 需要 DB schema / RLS / grant / policy / role 變更。
- 測試環境無法執行 formatter regression 或 side-effect gate。

## 本輪停止條件

完成到以下範圍即停止:

- 只抽出 Telegram 使用者可見 display/report assembly。
- 保留 formatTelegramMessages 相容入口。
- Side-effect gate 證明 presentation module 無 DB / evidence write import 或 call。
- 三則 messages 關鍵 fixture regression 通過。
- 無有效進場不顯示最強標的。
- maturity gate 仍為 100。
- version 更新到 v20.4.21 且與 header / 常量一致。

以下旁支只記待辦，不納入本輪:

- 更完整的 strategy / presentation 分層設計。
- 所有 generator helper 的全量搬移。
- 報文文案重寫。
- 新增策略指標。
- DB persistence 改造。
- live runner / Telegram delivery 流程改造。
- snapshot fixture 大規模重建。
