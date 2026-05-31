# TASK: Market Theme Historical Fetch 2026-05 And Evidence Dedupe

## 任務狀態

- task_id: market-theme-history-fetch-2026-05
- 任務類型: risk_patch
- 狀態: ready_for_tech
- 版本建議: none
- QA 分級建議: L3
- Owner 問題: production DB 的 market/theme 五月資料目前是 latest-only，不是 2026-05 歷史資料；market_theme_confirmed_evidence 還有 duplicate business-key groups，導致 correction audit 不能作為可信歷史證據。

## 使用者可見結果

完成後，Owner / Architect 用下列 read-only audit 可看到 market/theme 五月 coverage 不再是只有 2026-05-29，且 confirmed evidence duplicate groups 已清零或有明確可驗的保留規則：

arch -arm64 .venv/bin/python scripts/smoke_market_theme_evidence_readonly.py --correction-audit-json --limit 20000

本任務不改 Telegram / UI 報文；使用者可見結果是 audit JSON 與 Tech/QA 交付摘要。

## 非目標

- 不改策略買賣邏輯、分數、排序或 Telegram 文案。
- 不新增 market/theme 策略功能。
- 不把 sector_theme_members 當 daily history 回填。
- 不手寫普通 production DML。
- 不造假資料、不用 local cache / runtime dict / agent 對話當 production history。
- 不做 DB schema / index / constraint / RLS / grant / policy 變更；若必要，先 blocked 並輸出 SQL 給 Owner。

## 影響模組

Tech 需在主 repo 中定位既有 repo script / service API，最小範圍完成：

- market/theme historical fetch 或 backfill script / service path。
- production DB 寫入 path，僅限既有 approved interface。
- market_theme_index_daily_bars 五月歷史資料寫入。
- market_theme_confirmed_evidence 五月 confirmed evidence 寫入與 duplicate business-key group 處理。
- scripts/smoke_market_theme_evidence_readonly.py 只作驗收工具；除非 audit 本身缺必要欄位或錯判，否則不改 audit 口徑。

## 直接消費者

- Architect / Owner 的 correction audit flow。
- scripts/smoke_market_theme_evidence_readonly.py --correction-audit-json --limit 20000。
- 後續 evidence chain / market-theme 消費者，只能在本任務驗收完成後再擴張。

## 已存在且不得回退的契約

- production runner 視為無狀態；跨日歷史證據必須來自 production DB 或 Owner 指定持久來源。
- 非 schema data write / backfill 必須走既有 repo script 或 approved service API。
- 缺 source、source-error、欄位不足或可信度不足時 fail closed，不得補假資料。
- daily_signal_snapshot 五月歷史已完成，不納入本輪回填。
- sector_theme_members 是 mapping source，不是 daily history。
- 目前 baseline：
- market_theme_confirmed_evidence: 18 rows only 2026-05-29，9 duplicate business-key groups。
- market_theme_index_daily_bars: 10 rows only 2026-05-29。
- sector_theme_members: 12 active mapping rows, valid_from=2026-01-01，僅可作 mapping。
- 若 Tech 無法從既有 code / audit 中確認 duplicate business-key 定義，必須 blocked，列出表欄位與候選 key，不得自行假設並寫入 production。

## 輸出契約

Tech 交付的 CHANGELOG.md 必須說明：

- 使用的真實資料來源與 fetch path。
- 寫入介面：repo script 或 service API 名稱、參數、執行方式。
- 寫入範圍：
- market_theme_index_daily_bars 覆蓋 2026-05 可得交易日，不可只有 latest date。
- market_theme_confirmed_evidence 覆蓋 2026-05 可得交易日，不可只有 latest date。
- duplicate business-key 處理規則：
- 預設目標是 duplicate groups 清零。
- 若保留多筆，必須列出 business key、保留理由、audit 如何不再把它判為錯誤。
- read-after-write 驗證結果，至少包含 audit JSON 中 market/theme coverage、date range、row count、duplicate groups。
- 若有 source gaps，需列出缺哪些日期、來源回應、是否 fail closed。

## 驗收條件

1. 用真實來源經 repo script / service API 完成 production 寫入，不手寫普通 DML。
2. market_theme_index_daily_bars 的 2026-05 production coverage 不再只有 2026-05-29；應覆蓋來源可得的五月交易日，預期對齊 2026-05-04 到 2026-05-29 的 20 個交易日，除非真實來源明確缺日。
3. market_theme_confirmed_evidence 的 2026-05 production coverage 不再只有 2026-05-29。
4. market_theme_confirmed_evidence duplicate business-key groups 清零；若未清零，必須有明確保留規則且 audit JSON 不能再把它當未處理 duplicate 問題。
5. sector_theme_members 只作 mapping source；驗收不得把其 valid_from=2026-01-01 rows 算成五月 daily history。
6. 重跑：

arch -arm64 .venv/bin/python scripts/smoke_market_theme_evidence_readonly.py --correction-audit-json --limit 20000

結果必須顯示 market/theme 五月 coverage 不再 latest-only，且 duplicate groups 清零或符合保留規則。
7. QA 必須補一個 Tech 未覆蓋的反證路徑，例如：確認 source gap 不被假資料填滿、確認 duplicate key 不只是被 audit 忽略、或確認 sector_theme_members 沒被算作 daily history。

## 範例或 fixture

驗收 JSON 形狀需能支持下列判讀，欄位名以現有 audit 實際輸出為準：

{
"market_theme_index_daily_bars": {
"history_coverage": {
"conclusion": "covered",
"date_range": ["2026-05-04", "2026-05-29"],
"latest_only": false
}
},
"market_theme_confirmed_evidence": {
"history_coverage": {
"conclusion": "covered",
"latest_only": false
},
"duplicate_business_key_groups": 0
},
"sector_theme_members": {
"role": "mapping_source",
"counts_as_daily_history": false
}
}

若真實來源缺部分交易日，範例可改為 partial，但 Tech/QA 必須列出每個缺日與 source evidence；不得宣告完整 covered。

## 明確禁止事項

- 禁止手寫普通 production DML 直接 insert/update/delete。
- 禁止用假資料、推測資料、local cache 或單日 latest rows 複製成歷史。
- 禁止把 sector_theme_members 當 daily bars 或 confirmed evidence history。
- 禁止未經 Owner 先審 SQL 就做 schema、index、constraint、RLS、grant、policy、role 變更。
- 禁止 live Telegram delivery。
- 禁止把 smoke / integrity check 單純通過升格為「production 五月資料已完成」，必須對齊 audit coverage 與 duplicate 結果。

## 阻塞條件

Tech 必須 blocked 並回報，若出現任一情況：

- 找不到既有 repo script / service API 可安全寫入 production market/theme history。
- 需要 schema / index / constraint / RLS / grant / policy / role 變更。
- 真實來源沒有 2026-05 歷史資料或來源回應不可驗。
- 無法確認 market_theme_confirmed_evidence duplicate business-key 定義。
- production credentials / 權限 / source 讀寫失敗。
- audit output 無法區分 latest-only、source gap、duplicate groups。

## 本輪停止條件

完成範圍到「2026-05 market/theme 歷史抓取寫入 + confirmed evidence duplicate 處理 + read-only audit 驗收」為止。

旁支問題只記待辦，不納入本輪：

- 後續 evidence chain 功能擴張。
- 策略是否消費 market/theme history。
- Telegram 報文改版。
- DB schema 正規化或 constraint 補強。
- 其他月份或全歷史 backfill。
