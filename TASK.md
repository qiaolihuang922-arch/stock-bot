# TASK: Render 啟動時 market/theme evidence freshness check 與幂等補寫

## 任務狀態

- task_id: render_market_theme_evidence_freshness_20260603
- 任務類型: risk_patch
- 狀態: ready_for_tech
- 版本建議: 需升版使用者可見 runner / CLI log 版本或流程版本；若現有專案已有 report / runner version 常量，不得回退。
- QA 分級建議: L3

## Owner 問題

Render 不是手動 GitHub Action，而是高頻每 5 分鐘啟動。現有 market/theme evidence 寫入流程在 Render runner 場景下可能漏寫 market_theme_confirmed_evidence / market_theme_index_daily_bars，導致後續報文或策略讀不到最近交易
日 evidence。

本輪要補一個 Render/runner 每次啟動可呼叫的幂等 freshness check 流程：檢查最近 N 個交易日預設 5 日是否缺 evidence；已完整寫入的日期跳過；缺失且已過安全寫入時間才補寫；未到時間只讀不寫；寫後 read-after-write；任一日期失
敗要 fail closed 並明確 log。

## 使用者可見結果

- Render 每次啟動 runner 前會先執行 market/theme evidence freshness check。
- 最近 N 個交易日 evidence 完整時，不重寫、不覆蓋、不產生誤導成功。
- 最近 N 個交易日缺 evidence 且已過台北時間安全寫入時間，會透過既有 approved script/interface 補寫並驗證。
- 未到安全寫入時間時只檢查、不寫入，log 明確顯示 skipped-by-time。
- 若任一日期讀取、補寫或 read-after-write 失敗，runner 回傳 fail closed，不靜默進入使用者報文流程。
- 手動 backfill workflow/CLI 可使用 start_date / end_date，不再預設鎖死 2026-05-04~2026-05-29 或 May-only。

## 非目標

- 不改 DB schema、RLS、grant、policy、role、index、constraint。
- 不改 RR 公式、策略核心、買賣判斷、持倉狀態機。
- 不做 live Telegram delivery。
- 不手寫 production DML。
- 不新增另一套 production source-of-truth。
- 不把日期 2026-06-01~2026-06-03 寫死在產品代碼；這些日期只能作為驗收 / probe / backfill fixture。
- 不全量重跑歷史資料，不處理本輪以外的 market/theme 資料品質問題。

## 影響模組與直接消費者

- 影響模組:
- Render / runner 啟動流程中的 preflight 或 freshness check hook。
- market/theme evidence 既有 approved upsert interface / script。
- market/theme index daily bars 既有 approved upsert interface / script。
- 手動 backfill workflow / CLI 的日期參數處理。
- runner log / exit status / artifact summary。
- 直接消費者:
- Render 高頻啟動 runner。
- 報文 runner 在產生 Telegram 報文前讀取 market/theme evidence 的流程。
- 手動 backfill 操作者。
- QA replay / probe 腳本。

## 輸出契約

- Freshness check 必須可由 Render/runner 每次啟動呼叫，且幂等。
- 預設檢查最近 N=5 個交易日；N 可由 env 或 CLI/config 覆寫。
- 安全寫入時間預設為台北時間 14:00；可由 env 覆寫。
- 每個 trade_date 對兩類 evidence 分別檢查:
- market_theme_confirmed_evidence
- market_theme_index_daily_bars
- Business key 已完整存在時:
- 不 upsert。
- log 狀態為 already-complete 或等價明確語意。
- 缺失且未到安全寫入時間:
- 只讀不寫。
- log 狀態為 skipped-before-safe-write-time 或等價明確語意。
- 不視為成功補寫；但若流程契約允許 runner 繼續，必須明確區分「未到時間所以不寫」與「資料完整」。
- 缺失且已到安全寫入時間:
- 只能呼叫既有 approved upsert/read-after-write interface 或 approved repo script。
- 寫入後必須 read-after-write 驗證 business key 完整。
- log 狀態為 backfilled-and-verified 或等價明確語意。
- 任一日期 / 任一資料類型發生 source-error、upsert-error、read-after-write mismatch、缺必要欄位:
- exit / return 必須 fail closed。
- log 必須包含 trade_date、資料類型、錯誤階段、可重跑線索。
- 不得靜默吞錯後繼續宣告 freshness ok。
- Backfill workflow / CLI:
- 必須接受 start_date / end_date。
- 不得保留 May-only 預設鎖定。
- 未給日期時可使用既有安全預設，但不得阻擋 2026-06-01~2026-06-03 這類後續日期。

## 版本契約

- 若 runner / report header / CLI 有版本字串，需同步升版或明確記錄本次流程版本。
- 不得回退既有使用者可見版本字串。
- 不得改變 Telegram 報文內容格式，除非現有 runner log/version 是報文前置可見資訊；本輪不是報文文案任務。

## 已存在且不得回退的契約

- Production DB schema 不變。
- Production 寫入必須走既有 approved upsert/read-after-write interface 或 approved script。
- Runner 視為無狀態；跨日 evidence 狀態只能來自 production DB 或 Owner 指定 source-of-truth。
- 缺資料、source-error、欄位不足或可信度不足時必須 fail closed。
- Live Telegram delivery 需 Owner 單獨批准，本輪不得觸發。
- TASK.md -> CHANGELOG.md -> QA_REPORT.md 交付鏈不得跳過 Tech / QA。

## 驗收條件

1. 已存在日期跳過不重寫:
- fixture 中某 trade_date 兩類 evidence 均完整。
- freshness check 結果為 skipped/already-complete。
- approved upsert interface 未被呼叫。
- runner 不回報補寫成功。
2. 缺失日期在台北 14:00 後補寫:
- fixture 中某 trade_date 缺一類或兩類 evidence。
- 模擬時間為台北 14:00 後。
- 流程呼叫既有 approved upsert interface。
- 寫後 read-after-write 驗證完整。
- 結果明確列出 backfilled-and-verified。
3. 未到台北 14:00 不寫:
- fixture 中某 trade_date 缺 evidence。
- 模擬時間為台北 14:00 前。
- 流程只讀不寫，upsert interface 未被呼叫。
- log 明確顯示 skipped-before-safe-write-time。
- 不得把該日期標成 evidence complete。
4. 最近 5 個交易日中某天失敗會 fail closed:
- fixture 中 5 個交易日包含至少一個 read / upsert / read-after-write 失敗日期。
- 整體流程返回非成功狀態或 runner-blocking failure。
- log 指出失敗 trade_date、資料類型、錯誤階段。
- 不得靜默產出 freshness ok。
5. Backfill workflow / CLI 使用 start_date / end_date:
- 指定 2026-06-01 到 2026-06-03 可走已驗證 backfill 路徑。
- 代碼不寫死這三天。
- workflow/CLI 不再預設只處理 2026-05-04~2026-05-29。
- 若未提供日期，行為需有清楚文件或 log，且不影響顯式日期參數。

## 範例或 Fixture

- freshness check fixture:
- 2026-06-01: market_theme_confirmed_evidence 與 market_theme_index_daily_bars 已完整，預期跳過不重寫。
- 2026-06-02: 缺 evidence，模擬台北 14:05，預期補寫並 read-after-write 通過。
- 2026-06-03: 缺 evidence，模擬台北 13:55，預期只讀不寫。
- failure fixture:
- 最近 5 個交易日其中一天 upsert 成功但 read-after-write 缺 business key，預期 fail closed。
- backfill fixture:
- CLI/workflow input: start_date=2026-06-01, end_date=2026-06-03
- 預期不受 May-only 預設限制。

## 失敗標本與驗收路由

- 失敗標本:
- Render 每 5 分鐘啟動時，runner 沒有先做 freshness check，導致最近交易日 market/theme evidence 漏寫或缺失仍繼續產生後續流程。
- 手動 backfill 預設鎖在 2026-05-04~2026-05-29，無法覆蓋 2026-06-01~2026-06-03。
- 驗收路由:
- helper 層: 交易日窗口、safe write time、business key completeness 判斷。
- interface 層: 既有 approved upsert + read-after-write 被正確呼叫。
- runner 層: Render/runner 啟動可呼叫 freshness check，失敗會 blocking/fail closed。
- workflow/CLI 層: start_date / end_date 參數可控，不 May-only。
- production source 層: QA 若無權直接讀 production，需使用 Architect 提供的 read-only artifact；artifact 必須標明 source、版本、無 credential、無 write、無 live delivery。

## 明確禁止事項

- 禁止改 DB schema 或權限設定。
- 禁止手寫 production DML。
- 禁止 live Telegram delivery。
- 禁止修改 RR 公式或策略決策。
- 禁止把 local cache、runtime dict、agent 對話當跨日 evidence source-of-truth。
- 禁止吞錯後繼續宣告成功。
- 禁止把未到 14:00 的缺失日期補寫。
- 禁止用 synthetic fixture 取代 runner 層驗收；若只能測低層，Tech 必須標 partial。
- 禁止把 2026-06-01~2026-06-03 寫死在產品代碼。
- 禁止把本輪擴成全面資料清理或歷史重建。

## 阻塞條件

- 找不到既有 approved upsert/read-after-write interface 或 approved script，且需新增 interface 時，Tech 必須 blocked 或先明確最小新增接口，不得手寫 production DML。
- 無法判斷兩類 evidence 的 business key completeness 定義時，blocked，需 Architect 補充既有契約。
- 無法在 runner 啟動流程插入 freshness check 且沒有替代固定呼叫點時，blocked。
- 無法模擬台北時間或安全寫入時間設定時，blocked。
- QA 無法取得 runner artifact / replay artifact 且任務目標是 runner 場景，QA 結論最多 conditional pass，不得直接通過。

## 本輪停止條件

- 完成到以下範圍即停止:
- runner 每次啟動可呼叫幂等 freshness check。
- 最近 N 個交易日檢查、safe write time、skip/backfill/read-after-write/fail-closed 契約具備可重跑 probe。
- backfill workflow/CLI 支援 start_date / end_date，不再 May-only。
- 2026-06-01~2026-06-03 可作為驗收路徑覆蓋，但產品代碼不硬編碼。
- 以下旁支只記待辦，不納入本輪:
- 歷史全量 market/theme 資料稽核。
- evidence 內容品質重新評分。
- Telegram 報文版面或策略文案調整。
- DB schema 優化或新表設計。
- RR、買賣策略、持倉狀態機變更。
