# TASK: market/theme production evidence trend fresh-run consumption check

## 任務狀態

- task_id: market-theme-production-trend-consumption-check
- 任務類型: normal_patch
- 任務尺寸判斷: normal_patch
- 狀態: ready_for_tech
- 版本建議: patch
- 版本契約: 本輪不改 Telegram / report 使用者可見文案與 header，沿用目前 VERSION / Telegram header。若 Tech 發現必須修改 Telegram 報文、report 顯示、message list contract 或 header 才能完成驗收，必須 blocked 回 PM，不
得自行擴 scope。
- QA 分級建議: L2
- QA 升級原因: 本輪不做 production write / backfill / schema change，但要驗證正式 generator/report path、production DB source-of-truth 與 GitHub fresh runner 可重建性，需包含 local context cleared 反證。

## Owner 問題

上一輪已完成 market_theme_confirmed_evidence latest official rows 寫入與 read-after-write，並確認策略消費檢查可得到 uses_market_theme_confirmed_evidence_history=true。

但目前仍有三個缺口不能混在一起處理：

- 完整五月 market/theme history 仍缺真實 historical source。
- sector_theme_members 目前只有 latest source，不能假裝五月 history。
- market_theme_index_daily_bars 目前 skipped / not-consumed，不能因為表存在就視為有效策略來源。

本輪最小可交付只回答一個主問題：

正式 Telegram/report 生成路徑在 GitHub fresh runner / local context cleared 條件下，是否實際從 production market_theme_confirmed_evidence 讀取 trend，並能重建 evidence trend；還是只靠 local runtime、worktree cache、上
一輪 script report、或 daily_signal_snapshot 的間接結果。

## 使用者可見結果

Owner / Architect 會看到 Tech 的 CHANGELOG.md 與 QA 的 QA_REPORT.md 明確回答：

- 正式 generator/report path 是否讀取 production market_theme_confirmed_evidence trend。
- fresh runner / local context cleared 後是否仍可重建同樣 trend 判斷。
- 若不能成立，是缺 DB env、缺 production rows、缺 workflow env、consumer 沒接上、還是只在 backfill script report 裡成立。
- 本輪是否完全未做 DB schema、非 schema write、live Telegram、五月歷史偽造。

本輪不要求 Owner 手機 Telegram 看到新文案。手機閱讀路徑只做「既有報文不被改壞」檢查：若 existing report 已有 evidence trend 行，QA 應確認它仍不是買賣建議、不是可買誤導、且 header 版本未因本輪被偷偷改動。

## 非目標

- 不補完整五月 market/theme historical source。
- 不新增 historical provider。
- 不新增或修改 backfill workflow。
- 不改 Telegram/report 顯示文案、排序、header、message list contract。
- 不 live Telegram。
- 不改 DB schema、table、column、RLS、grant、policy、role。
- 不做任何 production data write，除非 Architect 另開任務且走既有 repo script/interface、dry-run、validation、read-after-write。
- 不把 daily_price / daily_signal_snapshot 回寫或 row count 當成本輪成果。
- 不把 sector_theme_members latest-only 資料回填成五月 history。
- 不把 market_theme_index_daily_bars 寫入或消費狀態改成完成，除非有明確直接 consumer 證據；本輪預設只記 not-consumed。
- 不改策略買賣門檻、持倉狀態機、watchlist。

## 影響模組

- 直接模組:
- 正式 Telegram/report generator 入口或其 smoke / fixture。
- services/market_theme_evidence_store.py 或等價 production read-only consumer。
- market/theme evidence provider / handoff path。
- GitHub runner / workflow env consumption 的只讀檢查或模擬 fresh-run 測試。
- 對應 tests / fixtures / diagnostics。
- 直接消費者:
- Owner / Architect：讀本輪驗證結果判斷 evidence chain 下一步是否能進入 historical source 任務。
- Telegram/report generator：正式報文生成 path。
- market/theme evidence trend provider：讀 production market_theme_confirmed_evidence historical rows。
- QA：反證 fresh runner 不依賴 local/runtime context。

## 輸出契約

本輪單一主輸出契約是「fresh-run consumption verification report」，可存在於 Tech 交付摘要、測試輸出、或 repo 既有 diagnostic script 的 JSON / dict 輸出中；不得要求 Owner 手動讀 DB。

必要欄位形狀：

{
"mode": "market-theme-production-trend-consumption-check",
"schema_change": false,
"data_write": false,
"live_telegram": false,
"source_of_truth": "production.market_theme_confirmed_evidence",
"local_context_cleared": true,
"fresh_runner_rebuild": "passed|failed|blocked",
"generator_consumption": {
"entrypoint": "official_telegram_or_report_generation_path",
"uses_market_theme_confirmed_evidence_history": true,
"uses_only_daily_signal_snapshot": false,
"uses_runtime_or_local_cache_as_history": false,
"observed_days": 0,
"recent_supporting_days": 0,
"support_streak_days": 0
},
"table_status": {
"market_theme_confirmed_evidence": "consumed|missing-source|source-error|insufficient-data",
"sector_theme_members": "latest-only-blocked|not-used",
"market_theme_index_daily_bars": "not-consumed|not-used"
},
"blocked_reasons": []
}

已存在且不得回退的契約：

- market_theme_confirmed_evidence 才是本輪 trend consumption 的 production source-of-truth。
- uses_market_theme_confirmed_evidence_history=true 不能只在 backfill script report 中成立；必須在正式 generator/report path 或其等價 smoke 中成立。
- GitHub runner / fresh run 必須可由 production DB / mocked persistent DB rows 重建；local runtime、worktree cache、agent 對話、script report、Telegram text 不得當跨日記憶。
- daily_price / daily_signal_snapshot 不得被包裝成本輪 market/theme trend source。
- sector_theme_members latest-only 必須保持 blocked / skipped，不得回填五月。
- market_theme_index_daily_bars skipped / not-consumed 狀態不得被無證據改成 consumed。
- confirmed / ready evidence 只能來自 production DB 或 Owner-approved persistent source family。
- evidence trend 只可作 wording / 排序提示 / detail trace；不得放寬買點、覆蓋風控、或單獨把不可買變 BUY。
- 非 schema data write 只能走既有 repo script/interface，且必須 dry-run、validation、read-after-write；本輪預設不寫。
- live Telegram 不在本輪。

## 驗收條件

1. 正式 consumer 檢查

- Tech 必須定位並驗證正式 Telegram/report generation path 是否調用 production market_theme_confirmed_evidence trend consumer。
- 驗證不能只跑上一輪 backfill script 的 strategy_consumption_check。
- 結果必須明確列 uses_market_theme_confirmed_evidence_history、uses_only_daily_signal_snapshot、observed_days、recent_supporting_days、support_streak_days。

2. Fresh runner / local context cleared 反證

- QA 必須至少驗證一個 fresh-run 等價案例：清空 local runtime/context/cache 後，使用 production DB 或 mocked persistent DB rows 仍可重建 trend。
- 若關閉本地對話、清空 worktree runtime、或模擬 GitHub fresh runner 後無法重建，QA 必須 blocked。
- 若只能依賴 env 缺失時的 fail-closed 狀態，必須明確標為 missing-source / source-error / insufficient-data，不得宣告 consumed。

3. Source 邊界

- 測試或 fixture 必須證明 daily_signal_snapshot 存在時也不能被當成 market/theme trend source。
- sector_theme_members latest-only 仍應 blocked / skipped。
- market_theme_index_daily_bars 若沒有直接 consumer，仍應 not-consumed / skipped。

4. 使用者可見報文不變

- 本輪不改 Telegram/report 文案與 header。
- 若驗證過程產生 sample Telegram/report，QA 只需檢查既有 evidence trend 行不造成「可買」誤讀，且 header 版本未被本輪改動。
- 若 Tech 需要修改報文顯示才能讓 consumption 可見，必須 blocked 回 PM。

5. 停止條件

- 完成一條正式 generator/report path consumption 驗證。
- 完成一條 fresh runner / local context cleared 反證。
- 證明本輪沒有 schema change、data write、live Telegram、五月歷史偽造。
- 若發現缺 historical provider、缺 workflow env、或 report 顯示不足，只列入 blocked / follow-up，不納入本輪實作。

## 範例或 fixture

成功範例：

{
"mode": "market-theme-production-trend-consumption-check",
"schema_change": false,
"data_write": false,
"live_telegram": false,
"source_of_truth": "production.market_theme_confirmed_evidence",
"local_context_cleared": true,
"fresh_runner_rebuild": "passed",
"generator_consumption": {
"entrypoint": "official_report_generation",
"uses_market_theme_confirmed_evidence_history": true,
"uses_only_daily_signal_snapshot": false,
"uses_runtime_or_local_cache_as_history": false,
"observed_days": 1,
"recent_supporting_days": 1,
"support_streak_days": 1
},
"table_status": {
"market_theme_confirmed_evidence": "consumed",
"sector_theme_members": "latest-only-blocked",
"market_theme_index_daily_bars": "not-consumed"
},
"blocked_reasons": []
}

Blocked 範例：

{
"mode": "market-theme-production-trend-consumption-check",
"schema_change": false,
"data_write": false,
"live_telegram": false,
"source_of_truth": "production.market_theme_confirmed_evidence",
"local_context_cleared": true,
"fresh_runner_rebuild": "blocked",
"generator_consumption": {
"entrypoint": "official_report_generation",
"uses_market_theme_confirmed_evidence_history": false,
"uses_only_daily_signal_snapshot": true,
"uses_runtime_or_local_cache_as_history": true,
"observed_days": 0,
"recent_supporting_days": 0,
"support_streak_days": 0
},
"table_status": {
"market_theme_confirmed_evidence": "not-consumed",
"sector_theme_members": "latest-only-blocked",
"market_theme_index_daily_bars": "not-consumed"
},
"blocked_reasons": [
"official generator path does not consume production evidence trend",
"fresh runner rebuild depends on local/runtime context"
]
}

手機閱讀示例輸出形狀（僅用於確認未改壞既有報文，不要求新增）：

證據：production 趨勢已讀取，僅作背景追溯，不改買賣。
趨勢：近1個證據日｜連續1日支持

## 明確禁止事項

- Tech 不得偽造五月歷史。
- Tech 不得把 latest sector_theme_members 回填成五月 membership。
- Tech 不得把 daily_price / daily_signal_snapshot 回寫或 row count 當成本輪成果。
- Tech 不得 live Telegram。
- Tech 不得改 DB schema / RLS / grant / policy / role。
- Tech 不得直接手寫 production DML。
- Tech 不得把 local/runtime/cache/worktree/chat/report-derived payload 當 production history。
- Tech 不得為了通過驗收改策略買賣門檻。
- Tech 不得修改 Telegram/report 顯示 contract；若必須改，回 PM。
- QA 不得只重跑 Tech 命令；必須補 fresh runner / local context cleared 反證。
- QA 不得在缺 DB env、缺 rows、或 source-error 時宣告 consumption passed。

## 阻塞條件

- 無法辨識正式 Telegram/report generation entrypoint。
- 缺 production DB read env，且無法用 mocked persistent DB rows 做 fresh-run 等價驗證。
- 正式 generator/report path 沒有消費 market_theme_confirmed_evidence trend。
- Fresh runner / local context cleared 後只能靠 runtime/local context 重建 trend。
- 需要新增 historical provider、workflow、或報文顯示改動才可完成驗收。
- 發現 production rows 不足，只能產生 missing-source / insufficient-data，不能證明 consumed。
- 任何驗證需要 live Telegram、DB schema change、或 production write。

## 公開來源

- 本輪未使用公開網路資料；任務定義依據為 Owner 指示與目前專案摘要文件。
