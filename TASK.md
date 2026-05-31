# TASK: correction audit daily_signal_snapshot 歷史版本語義修正

## 任務狀態

- task_id：correction-audit-daily-signal-snapshot-version-semantics-2026-05
- 任務類型：normal_patch
- 狀態：ready_for_tech
- 版本建議：不升 Telegram 版本；本輪不改使用者可見 Telegram 報文。
- QA 分級建議：L2
- 任務尺寸判斷：不是 tiny_patch。雖然是單一主 bug，但會改 correction audit 的 blocked / diagnostic 輸出契約與下游判讀；不得擴成 market/theme 抓取、DB backfill、schema guard、策略重設或全量清理。

## Owner 問題

開始 market/theme 歷史抓取前，必須先修正 correction audit 對 daily_signal_snapshot 的語義判斷。

正確語義：

- daily_signal_snapshot 歷史資料是「每日當時版本」留存。
- 不要求舊五月資料回填成目前 core/generator.py VERSION。
- current VERSION 在舊五月 0 rows 只能作為 diagnostic / run-health 訊號。
- audit 不得把「current VERSION 舊五月 0 rows」當作歷史 coverage blocker。
- audit 不得要求或暗示需要 backfill 舊五月 current VERSION snapshot。

同時保持 market/theme historical coverage 仍 blocked：

- market_theme_confirmed_evidence 只有 2026-05-29 latest-only。
- market_theme_index_daily_bars 只有 2026-05-29 latest-only。
- sector_theme_members 是 mapping-only，不是五月 daily history。

完成本輪 correction audit 語義修正後，才能進入下一張 market/theme 歷史抓取任務。

## 使用者可見結果

Owner 看到的是 correction audit / full-integrity 類輸出的判讀被收斂：

- daily_signal_snapshot 五月歷史 coverage 可以用「全版本 / 當日版本留存」判斷。
- current VERSION 舊五月 0 rows 顯示為 diagnostic / run-health，不造成歷史 coverage blocked。
- 不再出現要求舊五月 current VERSION backfill 的文字、next_action 或 blocked_reason。
- market/theme 三表仍明確 blocked，不被 daily_signal_snapshot 修正誤放行。

本輪不是 Telegram / UI 任務，無手機閱讀路徑與 Telegram 示例輸出要求。

## 非目標

- 不抓取 market/theme 歷史資料。
- 不處理 market_theme_confirmed_evidence duplicate / dedupe。
- 不補寫或 backfill daily_signal_snapshot。
- 不補寫或 backfill market/theme 任一 production table。
- 不改 DB schema、RLS、grant、policy、role、index、constraint。
- 不改策略 decision、持倉建議、watchlist、交易狀態機。
- 不改 Telegram 報文版本、文案或 live delivery。
- 不把 market/theme latest-only / mapping-only 狀態改判為完成。
- 不把 Owner 的「開始」解讀成跳過 Tech / QA 或直接改代碼授權。

## 影響模組

- correction audit / full-integrity report 產生路徑。
- daily_signal_snapshot 五月 coverage 判讀邏輯。
- audit JSON / CLI 輸出中的 status、blocked_reason、next_action、diagnostic 欄位。
- market/theme coverage blocker 的 report wording。
- 相關測試或 fixture。

## 直接消費者

- Owner：判斷 correction audit 是否已正確區分 snapshot 歷史 coverage 與 current VERSION run-health。
- Architect：依 TASK / CHANGELOG / QA_REPORT 判斷能否進入下一張 market/theme 歷史抓取任務。
- Tech：只按本任務修正 audit 語義，不執行抓取、backfill 或 schema 改動。
- QA：反證 current VERSION 舊五月 0 rows 不再阻塞 snapshot 歷史 coverage，且 market/theme 仍 blocked。

## 輸出契約

correction audit / full-integrity JSON 或等價 report 必須維持單一輸出契約，至少包含以下語義欄位：

status: pass | blocked
blocked_reason: null | string
daily_signal_snapshot:
history_coverage:
basis: daily_version_as_recorded | insufficient_evidence
row_count_all_versions: number
date_min: YYYY-MM-DD | null
date_max: YYYY-MM-DD | null
distinct_trade_dates: number
version_distribution: map
conclusion: covered | partial | insufficient_evidence
current_version_run_health:
generator_version: string
may_row_count_for_current_version: number
diagnostic: current_version_old_month_zero_rows | current_version_rows_present | source_error
blocks_history_coverage: false
market_theme_historical_coverage:
market_theme_confirmed_evidence:
conclusion: latest_only | partial | complete | insufficient_evidence
market_theme_index_daily_bars:
conclusion: latest_only | partial | complete | insufficient_evidence
sector_theme_members:
conclusion: mapping_only | insufficient_evidence
next_action:
- market_theme_historical_fetch_required
- market_theme_dedupe_followup_required
- source_error_blocked

契約要求：

- daily_signal_snapshot.current_version_run_health.blocks_history_coverage 對舊五月 current VERSION 0 rows 必須是 false。
- blocked_reason 不得把 current VERSION 舊五月 0 rows 寫成 historical coverage blocker。
- next_action 不得包含或暗示 daily_signal_snapshot 舊五月 current VERSION backfill。
- 若 daily_signal_snapshot 全版本歷史資料本身讀不到、日期不足或 source-error，仍可 blocked，但原因必須是 source_error / insufficient_evidence / actual history coverage gap，不是 current VERSION 舊五月 0 rows。
- market/theme 三表若仍是 latest-only / mapping-only，整體進入 market/theme 抓取前的 readiness 必須保持 blocked。

## 驗收條件

1. 使用 production read-only 或既有 fixture 證明：daily_signal_snapshot 五月全版本存在歷史 rows，且 current VERSION 五月 0 rows 時，audit 不因 current VERSION 0 rows blocked。
2. report / JSON 仍顯示 current VERSION 五月 0 rows 為 diagnostic / run-health，且明確 blocks_history_coverage=false。
3. market/theme historical coverage 仍 blocked：market_theme_confirmed_evidence 與 market_theme_index_daily_bars 只有 2026-05-29 latest-only，sector_theme_members 是 mapping-only。
4. next_action 指向 market/theme historical fetch / dedupe follow-up，不得要求 daily_signal_snapshot backfill。
5. 不執行 production write、backfill、cleanup、schema/RLS/grant/policy/role/index 變更或 live Telegram。
6. 本輪停止條件：只要 correction audit 已正確區分 daily_signal_snapshot history coverage 與 current VERSION run-health，且 market/theme blocker 未被誤放行，即完成。本輪不追 market/theme 抓取實作、dedupe 實作、資料補寫
或報文調整。

## 範例或 fixture

### Case A：舊五月 current VERSION 0 rows 不阻塞 snapshot 歷史 coverage

status: blocked
blocked_reason: market_theme_historical_coverage_incomplete

daily_signal_snapshot:
history_coverage:
basis: daily_version_as_recorded
row_count_all_versions: 936
date_min: 2026-05-04
date_max: 2026-05-29
distinct_trade_dates: 20
version_distribution:
v20.4.5: 240
conclusion: covered
current_version_run_health:
generator_version: v20.4.6
may_row_count_for_current_version: 0
diagnostic: current_version_old_month_zero_rows
blocks_history_coverage: false

market_theme_historical_coverage:
market_theme_confirmed_evidence:
conclusion: latest_only
market_theme_index_daily_bars:
conclusion: latest_only
sector_theme_members:
conclusion: mapping_only

next_action:
- market_theme_historical_fetch_required
- market_theme_dedupe_followup_required

### Case B：snapshot source-error 才可阻塞 snapshot history

status: blocked
blocked_reason: daily_signal_snapshot_source_error

daily_signal_snapshot:
history_coverage:
basis: insufficient_evidence
conclusion: insufficient_evidence
current_version_run_health:
diagnostic: source_error
blocks_history_coverage: false

next_action:
- source_error_blocked

## 已存在且不得回退的契約

- production DB 是跨日狀態與歷史資料判斷的 source-of-truth。
- runner 視為無狀態；local/cache/runtime/worktree 不能當 production history。
- daily_signal_snapshot 歷史是按每日當時版本留存，不要求舊五月回填 current VERSION。
- current core/generator.py VERSION 舊五月 0 rows 只作 diagnostic / run-health，不作歷史 coverage blocker。
- market/theme historical coverage 目前仍 blocked；latest-only / mapping-only 不得稱為五月完整歷史。
- DB schema / RLS / grant / policy / role / index / constraint 變更需 Owner 事前確認。
- production write / cleanup / backfill 不在本輪授權內。
- live Telegram delivery 需 Owner 單獨批准。
- PM -> Tech -> QA 完整交付，不得跳過 QA。
- 證據不足時必須 blocked 或 insufficient_evidence，不得推論補齊。

## 明確禁止事項

- 禁止 production DB insert / update / delete。
- 禁止 backfill daily_signal_snapshot 或 market/theme tables。
- 禁止 schema、RLS、grant、policy、role、index、constraint 變更。
- 禁止 live Telegram。
- 禁止 market/theme 歷史抓取實作。
- 禁止 confirmed evidence dedupe 實作。
- 禁止把 current VERSION 舊五月 0 rows 作為 daily_signal_snapshot 歷史 coverage blocker。
- 禁止在 next_action 要求 daily_signal_snapshot 舊五月 current VERSION backfill。
- 禁止把 market/theme latest-only / mapping-only 說成完整 historical coverage。
- 禁止把 Owner 的「開始 / 繼續 / 處理 / 修復 / 檢查 / 清理 / 直接來」解讀成跳過 Tech / QA 或直接改代碼授權。

## 阻塞條件

Tech 遇到以下任一情況必須 blocked：

- 無法確認 correction audit 目前輸出契約或入口。
- 無法可靠區分 daily_signal_snapshot 全版本歷史 coverage 與 current VERSION run-health。
- 無法讀取 current core/generator.py VERSION，且輸出契約需要該值。
- production read-only / fixture 證據不足以驗證本輪語義。
- 修正必須依賴 production write、backfill、cleanup 或 schema 變更。
- 修正會誤放行 market/theme historical coverage。
- 需要改動策略 decision、Telegram live delivery 或 DB 結構才能完成。

## QA 分級建議

- QA level：L2
- QA 必須至少補一個 Tech 未覆蓋的反證案例：current VERSION 舊五月 0 rows 但全版本五月歷史存在，audit 不得因此 blocked。
- QA 必須檢查 market/theme blocker 沒有被本輪修正誤清除。
- QA 必須檢查 blocked_reason 與 next_action 沒有要求 daily_signal_snapshot backfill。
- QA 不得只重跑 Tech 命令；需檢查輸出語義是否會讓 Owner 誤讀為 market/theme 已完成或 snapshot 需要 backfill。
- QA 結論只能是 通過、阻塞、conditional pass。
