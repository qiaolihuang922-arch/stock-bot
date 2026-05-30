# TASK: market/theme 五月歷史回寫 source-of-truth 與策略消費閉環

## 任務狀態

- task_id: market-theme-may-history-backfill-gap
- 任務類型: risk_patch
- 狀態: ready_for_tech
- 任務尺寸判斷: risk_patch。理由是本輪涉及非 schema production data backfill、DB 污染防護、read-after-write、以及策略是否真的消費 market/theme history；不能當 tiny_patch，也不得擴成策略重設或全量資料平台重建。
- 版本建議: patch
- 版本契約: 本輪不改 Telegram 報文內容與 header，沿用目前 VERSION / Telegram header；若 Tech 實際改到 Telegram/CLI 使用者可見報文 header 或 message contract，必須 blocked 要求 PM 重寫版本契約。
- QA 分級建議: L3。原因是本輪碰 backfill / DB write path / strategy consumption，QA 必須驗證 dry-run、payload path、read-after-write、污染防護與 fresh runner consumption。

## Owner 問題

Owner 要開始做正確的 market/theme 歷史回寫：只回写真正有用、能和策略關聯、並被報文或證據鏈消費的資料。

本輪要回答並落地一個主問題：market_theme_confirmed_evidence、market_theme_index_daily_bars、sector_theme_members 是否能取得真實五月歷史並安全回寫，且回寫後策略 / evidence trend 確實消費這些 market/theme history；不能把
已存在的 daily_price / daily_signal_snapshot 五月 rows 重跑一遍當成果。

PM 產品結論：

- 五月 daily_price / daily_signal_snapshot 已有資料，本輪不得把重複回寫它們列為主要成果。
- market_theme_confirmed_evidence 是 evidence trend 的直接消費表；若能取得五月真實 historical source，應納入本輪 backfill。
- market_theme_index_daily_bars 與 sector_theme_members 只有在它們會被 confirmed evidence 生成、validation、或 strategy/report trace 直接消費時才回寫；若目前沒有直接消費者，Tech 只能補 dry-run/audit 說明，不得為了「看
起來完整」寫入無消費資料。
- 若五月 historical source 只能從 latest snapshot、runtime report、chat/log、daily_signal_snapshot 推論，必須 fail closed / blocked，不得製造假歷史。

## 使用者可見結果

Owner / Architect 會看到 repo script/interface 的 dry-run、validation、execute report 與 QA 報告，明確回答：

- 哪些 market/theme tables 有五月真實 source 可以回寫。
- 哪些 tables 因缺 historical source 或缺直接消費者而 blocked / skipped。
- 實際寫入範圍、row count、date coverage、duplicate/upsert conflict、污染防護結果。
- read-after-write 後，策略 / evidence chain 是否真的讀到 market_theme_confirmed_evidence historical trend，而不是只讀 daily_signal_snapshot。
- 若不能取得五月歷史，輸出 blocked / insufficient-source，並列缺少的 source，不輸出合成 rows。

本輪不是 Telegram 報文/UI 任務，不改手機報文；手機閱讀路徑不適用。若後續報文因 history trend 顯示改變，需另開 Telegram 任務。

## 非目標

- 不改 DB schema、table、column、RLS、grant、policy、role。
- 不 live Telegram。
- 不改策略核心買賣門檻、watchlist、持倉狀態機。
- 不把 daily_price / daily_signal_snapshot 五月重跑當成本輪成果。
- 不補 fake / synthetic / inferred market/theme history。
- 不用 runtime/local/cache/worktree/chat/report-derived artifact 當 historical source-of-truth。
- 不清理或刪除既有五月 daily_price / daily_signal_snapshot rows。
- 不做全量歷史平台、全市場資料湖、或跨年 backfill。
- 不新增人工 SQL 給 Owner 手動跑；非 schema data write 應走 repo script / approved service interface。

## 影響模組

- 直接模組:
- market/theme source audit / backfill script 或 service interface。
- market_theme_confirmed_evidence approved payload validation / write path。
- market_theme_index_daily_bars、sector_theme_members 的 source loader / validation / upsert path，如 repo 已有既有接口才可擴充。
- services/market_theme_evidence_store.py 或等價 read-only consumer，用來驗證 evidence trend consumption。
- workflow dispatch / backfill mode，只限新增或修正 market/theme backfill entrypoint，不重跑 signal backfill 當成果。
- 對應 tests / fixtures。
- 直接消費者:
- Architect / Owner：讀 dry-run / execute report 判斷五月 market/theme history 是否可用。
- market/theme evidence trend provider：讀 market_theme_confirmed_evidence historical rows。
- Telegram/report generator：只作既有 evidence trend 消費者驗證，不改報文 contract。
- QA：驗證 fresh runner 不靠 local runtime，也不只靠 daily_signal_snapshot。

## 輸出契約

單一主輸出契約：market/theme May backfill script/interface report，支援 dry-run、execute、validation、read-after-write。

必要 report 欄位：

{
"mode": "market-theme-history-backfill",
"date_range": {"start": "2026-05-01", "end": "2026-05-29"},
"write_execution": "dry-run|executed|disabled",
"live_telegram": false,
"schema_change": false,
"tables": [
{
"table": "market_theme_confirmed_evidence",
"source_of_truth": "owner_approved_persistent_or_official_historical_source",
"historical_source_status": "available|missing|partial|source-error|not-consumed",
"consumer_path": "market_theme_evidence_store.evidence_trend",
"candidate_rows": 0,
"validated_rows": 0,
"written_rows": 0,
"skipped_rows": 0,
"coverage": {"first_trade_date": null, "last_trade_date": null, "trade_dates": 0},
"duplicate_conflicts": 0,
"pollution_guard": "passed|blocked",
"read_after_write": "passed|not-run|blocked",
"status": "ready|executed|blocked|skipped"
}
],
"daily_price_signal_snapshot_rewrite": "forbidden_as_primary_result",
"strategy_consumption_check": {
"uses_market_theme_confirmed_evidence_history": true,
"uses_only_daily_signal_snapshot": false,
"observed_days": 0,
"support_streak_days": 0
},
"blocked_reasons": []
}

每張表的 source-of-truth 契約：

- market_theme_confirmed_evidence
- 真實 source-of-truth：production DB 中通過 validation 後的 market_theme_confirmed_evidence rows。
- 回寫候選來源：Owner-approved persistent source 或官方 historical source，且必須能提供 trade_date/as_of/market_index/sector_theme_key/watchlist_breadth/evidence_value/support_level/source_family/source_name/
lineage。
- 禁止來源：daily_signal_snapshot row count、個股 score、runtime report text、Telegram text、local cache、chat/log 推論。
- 直接消費者：evidence trend / provider / report detail trace。
- market_theme_index_daily_bars
- 真實 source-of-truth：官方或 Owner-approved market/theme index historical bars source。
- 必須有可驗證日期、index/theme key、OHLCV 或 repo 既有 contract 所需欄位。
- 只有在 confirmed evidence generation、validation、或 report trace 直接消費時才可寫入；否則 report not-consumed 並 skipped。
- sector_theme_members
- 真實 source-of-truth：官方或 Owner-approved sector/theme membership historical source。
- 必須能證明五月當日 membership，而不是用今日 membership 回填五月。
- 只有在 breadth / theme evidence 計算直接消費時才可寫入；若只能取得 latest membership，五月 history 必須 blocked 或標記 latest-only skipped。

已存在且不得回退的契約：

- daily_price / daily_signal_snapshot 五月資料已存在，不得把重複 backfill 它們當成本輪完成。
- cross_day_context 只讀 current-version daily_signal_snapshot 與 position_events；不得讓舊 snapshot 或 local runtime 影響 fresh runner 跨日狀態。
- confirmed / ready market/theme evidence 只能來自 production / persistent source family；runtime/local/cache/worktree/report-derived/chat/test fixture 不得 confirmed。
- market_theme_confirmed_evidence 缺 source 時必須 fail closed，不得 runtime fallback 成 confirmed。
- evidence trend 只可作 wording / 排序提示 / detail trace；不得放寬買點、覆蓋風控、或單獨把不可買變 BUY。
- 非 schema data write 可走既有 repo script/interface，但必須 dry-run、validation、duplicate/upsert guard、read-after-write；不得直接手寫 production DML。
- live Telegram 不在本輪。

## 驗收條件

1. Source audit 收斂
- Script dry-run 對三張表分別輸出 historical source availability、date coverage、consumer path、blocked/skipped reason。
- 若 source 只能取得 latest snapshot，五月回寫必須 blocked/skipped，不能用 latest row 套到五月日期。
- 若 sector_theme_members 無法證明五月當日 membership，不能回寫五月 membership history。
2. Backfill 範圍正確
- 本輪目標日期限定 2026-05-01 到 2026-05-29 的台股交易日。
- daily_price / daily_signal_snapshot 不得作為主要 write target；最多只可 read-only 檢查 row count / coverage，證明不是本輪成果。
- 每張 market/theme table 必須列 candidate_rows、validated_rows、written_rows、skipped_rows、duplicate_conflicts。
3. Write safety
- Dry-run 預設不寫 DB，輸出 write plan 與 validation result。
- Execute 必須走 repo script/interface 的明確 flag，例如 --write --confirm-write 或既有等價機制。
- Upsert/conflict key 必須防止同一 table、date、index/theme/source 重複污染；重跑同一日期範圍應 idempotent。
- 不輸出 secret、URL、key、hash、fingerprint。
4. Validation / pollution guard
- 缺 required fields、日期不在範圍、source family 不允許、lineage 不可追溯、或 membership/latest 混用時，該 row 必須 rejected。
- Validation report 必須區分 missing-source、source-error、partial-coverage、not-consumed、validated。
- 若五月只有部分交易日可取得真實 source，可 partial write 真實 rows，但必須明確列 missing dates；不得補 synthetic rows。
5. Read-after-write
- Execute 後必須 read-after-write 查回三張表本輪寫入範圍、row count、duplicate key count。
- 至少對 market_theme_confirmed_evidence 驗證 evidence trend consumer 可讀到五月 historical rows，並產生 observed_days / recent_supporting_days / support_streak_days 等 trend 訊號。
- QA 必須驗證策略 / report path 消費 market_theme_confirmed_evidence history，不得只驗 daily_signal_snapshot 存在。
6. Fresh runner consumption
- 在清空 local/runtime context 的 fresh run 或等價測試中，market/theme trend 仍能從 production DB / mocked persistent DB rows 重建。
- 若 fresh runner 只能靠 local file、worktree cache、對話記憶、或 runtime dict 重建，必須 blocked。

## 範例或 fixture

Blocked 範例：

{
"mode": "market-theme-history-backfill",
"date_range": {"start": "2026-05-01", "end": "2026-05-29"},
"write_execution": "disabled",
"live_telegram": false,
"tables": [
{
"table": "sector_theme_members",
"historical_source_status": "missing",
"source_of_truth": "official_or_owner_approved_historical_membership",
"consumer_path": "watchlist_breadth_generation",
"candidate_rows": 0,
"validated_rows": 0,
"written_rows": 0,
"status": "blocked",
"blocked_reasons": ["only latest membership available; cannot prove May membership"]
}
],
"strategy_consumption_check": {
"uses_market_theme_confirmed_evidence_history": false,
"uses_only_daily_signal_snapshot": false
}
}

Successful partial write 範例：

{
"mode": "market-theme-history-backfill",
"date_range": {"start": "2026-05-01", "end": "2026-05-29"},
"write_execution": "executed",
"live_telegram": false,
"schema_change": false,
"tables": [
{
"table": "market_theme_confirmed_evidence",
"historical_source_status": "partial",
"candidate_rows": 9,
"validated_rows": 9,
"written_rows": 9,
"skipped_rows": 0,
"duplicate_conflicts": 0,
"coverage": {"first_trade_date": "2026-05-18", "last_trade_date": "2026-05-29", "trade_dates": 9},
"read_after_write": "passed",
"status": "executed"
}
],
"daily_price_signal_snapshot_rewrite": "not-performed",
"strategy_consumption_check": {
"uses_market_theme_confirmed_evidence_history": true,
"uses_only_daily_signal_snapshot": false,
"observed_days": 9,
"recent_supporting_days": 5,
"support_streak_days": 3
}
}

## 明確禁止事項

- 禁止改 DB schema、table、column、RLS、grant、policy、role。
- 禁止 live Telegram。
- 禁止改策略 BUY/SELL/RR/停損停利核心門檻。
- 禁止把 daily_price / daily_signal_snapshot 重複回寫包裝成本輪成果。
- 禁止用 latest market/theme snapshot 偽裝五月歷史。
- 禁止 fake、synthetic、runtime、local cache、worktree、chat、Telegram text、report-derived data 生成 confirmed history。
- 禁止直接手寫 production DML；必須走 repo script/interface。
- 禁止無 dry-run / 無 validation / 無 read-after-write 的 production write。
- 禁止讀取或輸出 .env、*.pem、~/.aws/credentials、~/.ssh/*、token、browser profile、secret value。
- 禁止為了通過 QA 擴大成全量回測、全市場 ingestion、或 Telegram 文案改版。

## 阻塞條件

- 無法取得五月 historical source，只能取得 latest source。
- source 缺 trade_date/as_of 或日期 lineage 不可信。
- sector_theme_members 不能證明五月當日 membership。
- market_theme_index_daily_bars 沒有官方 / Owner-approved historical bars source。
- market_theme_confirmed_evidence payload 缺 required fields 或 source family 不允許。
- 三張表沒有任何直接消費者，或 Tech 無法證明寫入後會被 strategy / evidence chain 讀取。
- 必須新增 schema、view、function、RLS、grant、policy、role 才能完成。
- 必須依賴 live Telegram 才能驗證。
- 測試只能靠不可 mock 的 production side effect 或本地對話記憶才能通過。

## 本輪停止條件

- 完成三張 market/theme tables 的 source audit、consumer audit、dry-run report。
- 對有真實五月 source 且有直接消費者的 table，完成 validation、idempotent write path、read-after-write。
- 對缺 source 或缺消費者的 table，明確輸出 blocked/skipped reason，不寫假 rows。
- QA 證明 market/theme evidence trend 消費 market_theme_confirmed_evidence history，且不是只消費 daily_signal_snapshot。
- QA 完成 fresh runner / no local context 反證。
- 旁支問題只記待辦，不納入本輪：更多月份 backfill、Telegram 顯示改版、策略門檻調整、schema 擴充、RLS/role 設計、全量 replay/backtest。
