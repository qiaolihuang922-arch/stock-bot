# TASK: Evidence Phase 5 Read-only Confirmed Evidence Loader

## 任務狀態

- task_id: evidence_phase_5_readonly_confirmed_evidence_loader
- 任務類型：normal_patch
- 狀態：ready_for_tech
- 版本建議：patch，Telegram / CLI 使用者可見版本升至 v20.4.3
- QA 分級建議：L2
- 任務尺寸判斷：normal_patch
- 理由：本輪不是單一文案 tiny patch；會新增 read-only DB consumption / loader，並接到 GitHub fresh runner 產生 Telegram 報文的 market/theme evidence source contract。
- 不升為 risk_patch：本輪不改策略買賣門檻、不改 DB schema、不寫 production DB、不做 backfill、不 live Telegram。

## Owner 問題

上一輪 PM/TASK 錯把 support_level 寫成 strong，與已驗過的 production schema 不符。Owner 要重跑 Evidence Phase 5：開發 read-only confirmed evidence loader，讓 GitHub / fresh runner 生成 TG 報文時，從 production table
public.market_theme_confirmed_evidence 讀取 market/theme confirmed evidence 的唯一持久 source-of-truth。

本輪必須修正契約：support_level 不得接受 strong。fresh confirmed row 只有在同時滿足：

- support_level in ('confirmed', 'supporting')
- evidence_status = 'confirmed'
- freshness = 'fresh'

才可輸出 confirmed。

## 使用者可見結果

Owner 在手機打開 Telegram 報文時，market/theme evidence 區塊會依 production DB read-only loader 顯示：

- 有 fresh confirmed production row：可顯示 confirmed evidence 摘要。
- DB env 缺失、查詢錯誤、無資料或資料不足：只能顯示 fail-closed 狀態，不得假裝 confirmed。
- 不會出現或接受 support_level=strong 的證據狀態。

手機閱讀路徑：

1. Header 顯示 v20.4.3。
2. 主決策 summary 仍先回答今日能不能買、持倉先處理什麼。
3. Evidence 摘要只用短句補充 production confirmed evidence 是否成立。
4. 若 evidence 不足，顯示限制句，不把缺資料誤寫成市場偏弱或 confirmed。

## 非目標

- 不改 production DB schema。
- 不改 RLS policy。
- 不做 live Supabase write。
- 不做 backfill。
- 不做 live Telegram delivery。
- 不改策略核心買賣門檻。
- 不新增 local/runtime/report-derived confirmed fallback。
- 不接受、轉譯或兼容 support_level=strong。
- 不重做 Evidence Phase 4 schema verification。
- 不清理全 repo、不重構 unrelated evidence pipeline。

## 影響模組

- Read-only DB loader / data access：新增或擴充讀取 public.market_theme_confirmed_evidence 的 production loader。
- Market/theme evidence provider：將 loader 結果接入現有 evidence source contract。
- Telegram formatter / generator：使用 loader 結果輸出 evidence summary 與 fail-closed wording。
- GitHub / fresh runner path：fresh run 必須能只靠 production DB 重建 confirmed evidence 判斷。
- 測試：loader contract、provider consumer、Telegram evidence summary / snapshot 類測試。

## 直接消費者

- core/market_theme_evidence.py 或等價 market/theme evidence provider。
- core/generator.py 或等價 Telegram 報文產生器。
- GitHub fresh runner / scheduled report generation path。
- QA fixture / tests that validate evidence summary and fail-closed source contract.

## 輸出契約

### Source-of-truth

- public.market_theme_confirmed_evidence 是本輪 market/theme confirmed evidence 的唯一持久 source-of-truth。
- GitHub fresh runner 必須可從 production DB read-only query 重建相同 confirmed / fail-closed 判斷。
- local file、runtime dict、report-derived text、cache、worktree fixture、agent 對話內容不得成為 confirmed source。

### Production schema enum contract

已存在且不得回退的契約：

- support_level 只允許：
- confirmed
- supporting
- weak
- invalidated
- support_level=strong 不存在於 production schema contract，且不得出現在 TASK、code、test、fixture、validator、fallback mapping 或文件範例中作為可接受值。
- Fresh confirmed row 判定只能是：
- support_level in ('confirmed', 'supporting')
- evidence_status = 'confirmed'
- freshness = 'fresh'

### Loader result contract

Loader / provider 對下游輸出必須能區分：

- confirmed：只在 fresh confirmed row 條件全部成立時輸出。
- absent：production table 可讀但沒有可用 row。
- missing-source：缺 DB env、缺 production source config，或 runner 無法建立 production source。
- source-error：DB query error、permission error、timeout、schema mismatch、unexpected enum value。
- insufficient-data：row 存在但缺 required fields，或 freshness / evidence_status / support_level 不足以 confirmed。

Fail-closed 規則：

- 缺 DB env 不得 confirmed。
- 查詢錯誤不得 confirmed。
- 無資料不得 confirmed。
- 資料不足不得 confirmed。
- enum unexpected，包括 support_level=strong，不得 confirmed；應視為 source-error 或 insufficient-data，由 Tech 依現有 error model 收斂，但不可 silent fallback。

## 版本契約

- 本輪改變 GitHub fresh runner / Telegram 使用者可見 evidence source 行為，版本升至 v20.4.3。
- Tech 必須同步 core/generator.py 的 VERSION 或等價 header 常量與相關測試期望。
- QA 必須核對實際輸出 header 顯示 v20.4.3。

## 驗收條件

1. Fresh confirmed production row 可 confirmed：
- fixture row support_level=confirmed 或 supporting
- evidence_status=confirmed
- freshness=fresh
- required fields 足夠
- loader / provider 輸出 confirmed
- Telegram evidence summary 顯示 production confirmed evidence，不使用 local/runtime fallback。
2. Fail-closed cases 不得 confirmed：
- 缺 DB env -> missing-source
- query error -> source-error
- no rows -> absent
- row 缺 required fields -> insufficient-data
- freshness != fresh -> 不得 confirmed
- evidence_status != confirmed -> 不得 confirmed
- support_level in ('weak', 'invalidated') -> 不得 confirmed
3. strong 禁止契約：
- code、tests、fixtures、validators、docs changed in this task 不得把 strong 當作 accepted support_level。
- 若測試故意注入 support_level=strong，期望結果必須是 fail-closed，不得 normalized to confirmed / supporting。
4. Fresh runner 可重建：
- 在 clean / fresh run、無本地 cache、無 agent runtime context 時，只靠 production DB read-only source 得出相同 confirmed / fail-closed 結果。
- Tech 必須在 CHANGELOG.md 說明本輪無新增本地持久狀態，任何 helper/cache 是否只限同一次 run。
5. 直接消費者同步：
- market/theme evidence provider 使用 loader contract。
- Telegram formatter 使用 provider result，不直接讀 local fallback。
- 使用者可見 fail-closed wording 短句、手機可讀，不輸出 debug enum dump。

## 範例或 fixture

### Fixture A: confirmed

Input row shape:

market_index=TAIEX
sector_theme_key=semiconductor
trade_date=2026-05-29
as_of=2026-05-29T...
freshness=fresh
evidence_status=confirmed
support_level=supporting
evidence_value=...
source_family=production_db
lineage=...

Expected loader/provider:

status=confirmed
source_of_truth=production_db
support_level=supporting
freshness=fresh
evidence_status=confirmed

Expected Telegram shape:

版本：v20.4.3
證據：production confirmed，市場/題材支持成立。

### Fixture B: unsupported enum must fail closed

Input row shape:

freshness=fresh
evidence_status=confirmed
support_level=strong
source_family=production_db

Expected result:

status=source-error 或 insufficient-data
confirmed=false

Expected Telegram shape:

證據：production 來源不足，不作確認。

### Fixture C: missing DB source

Input:

DB env missing 或 production connection unavailable

Expected result:

status=missing-source
confirmed=false

Expected Telegram shape:

證據：production 來源不足，不作確認。

## 明確禁止事項

- 禁止 live Supabase write。
- 禁止 backfill。
- 禁止修改 RLS。
- 禁止 live Telegram delivery。
- 禁止新增或使用 local/runtime/report-derived fake confirmed fallback。
- 禁止在任何契約中接受 support_level=strong。
- 禁止把 weak、invalidated、stale row、non-confirmed status 包裝成 confirmed。
- 禁止改策略 BUY / SELL / 加減碼門檻。
- 禁止把缺資料解讀成市場不強；只能輸出 source absent / missing / error / insufficient。
- 禁止順手重構 unrelated DB layer、watchlist、position state、backfill scripts。

## 阻塞條件

Tech 必須 blocked，而不是自行假設：

- 找不到可接入的 production DB read-only config pattern。
- 現有 schema summary 與 Owner 指定 enum 衝突。
- 直接消費者無法在不改策略門檻的情況下接入 loader。
- 無法區分 missing-source、source-error、absent、insufficient-data。
- 需要 live DB write、RLS change、backfill 或 live Telegram 才能完成本輪驗收。
- 任何上游文件仍要求或暗示 support_level=strong 是合法值。

## 本輪停止條件

本輪完成到以下範圍即停止：

- Read-only loader contract 已實作。
- Direct consumers 已同步。
- Telegram evidence summary 可用 fixture 驗證 confirmed / fail-closed。
- support_level=strong 不再被任何本輪 contract 接受。
- L2 QA 完成 clean/fresh run 反證與直接消費者驗證。

以下旁支只記待辦，不納入本輪：

- writer / ingestion。
- production backfill。
- RLS policy。
- schema migration update。
- live Telegram delivery。
- 策略門檻調整。
- 外部新聞 / 題材 provider。
- 全量 replay / full pytest，除非 QA 發現本輪 contract 風險必須升級並說明停止條件。

## QA 分級建議

- 建議：L2
- 必驗：
- loader unit / contract tests
- provider consumer tests
- Telegram evidence summary fixture / snapshot
- clean/fresh run 反證：清空 local/runtime/cache context 後不得 fake confirmed
- repo/test fixture 掃描：本輪契約不得接受 support_level=strong
- 不要求：
- live Supabase write
- live Telegram
- backfill dry-run
- full pytest，除非 L2 發現 contract 擴散風險
