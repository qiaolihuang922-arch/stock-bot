# CHANGELOG: Evidence Chain Production Closure Gap Assessment

## 任務尺寸與風險

- 任務尺寸：risk_patch。
- 判斷原因：本輪確認 production closure 下一步是否需要擴字段 / 擴表，並修正 QA 攔下的 read-only loader source-of-truth guard；若不修，非 production source row 可能被誤判為 Telegram confirmed。
- 最小改動策略：保留既有 candidate diff，不重置 worktree；只補 no-schema-change assessment、read-only smoke schema_decision、loader source_family allowlist/denylist guard 與局部測試。

## 修改內容

- 新增 production closure gap assessment artifact：
  - `schema_decision: no-schema-change`
  - current table contract
  - required for read-only smoke
  - required for manual backfill
  - production closure matrix
  - next manual steps / not done
- read-only smoke output 補 `schema_decision: no-schema-change`。
- read-only loader confirmed 判定收緊：
  - 只接受 `production_db`、`owner_approved_persistent`、`market_data`。
  - 拒絕 `local`、`runtime`、`cache`、`worktree`、`report-derived` / `report_derived`、`synthetic`、`default`、`test`、`fixture` 等 source family。
  - 即使 forbidden source row 同時是 `fresh + confirmed + supporting/confirmed`，也必須 fail closed。
- 補測試覆蓋 forbidden source fail closed、allowed persistent source confirmed、smoke CLI schema decision。

## 修改檔案

- `docs/handoff/evidence_chain_production_closure_gap_assessment.md`
- `docs/handoff/evidence_chain_market_theme_ops_artifacts.md`
- `services/market_theme_evidence_store.py`
- `scripts/smoke_market_theme_evidence_readonly.py`
- `tests/test_market_theme_evidence_handoff.py`

## Schema Decision

schema_decision: no-schema-change

理由：

- 現有 schema 已包含 loader、manual backfill、read-only smoke 所需欄位。
- loader confirmed contract 已對齊既有欄位：`support_level in ('confirmed','supporting')`、`evidence_status='confirmed'`、`freshness='fresh'`。
- JSONB 欄位 `evidence_value`、`watchlist_breadth`、`lineage`、`metadata` 足以承接 evidence / lineage payload。
- read-only smoke 只需要 SELECT 既有表與既有欄位。
- manual backfill/upsert 已可用既有 unique key：`trade_date, market_index, sector_theme_key, source_family, source_name, as_of`。
- 本輪缺口不是 schema，而是 loader 必須拒絕 production table 中標記為 local/runtime/test 的不可信 rows；已用 source_family guard 修正。

## Production Closure Matrix

| area | repo-side status | remaining gap |
| --- | --- | --- |
| schema | no-schema-change | Owner 仍需保持 production table 與 verified schema 一致 |
| ingestion validation | dry-run exists and fake/local/runtime/test sources fail closed | 尚未啟用 live ingestion provider |
| manual backfill | manual SQL template / validation-to-SQL path exists | Owner 需另行批准 source、placeholder、執行 |
| read-only smoke | uses `SUPABASE_READONLY_KEY` only and prints schema decision | 需 Owner 提供 read-only env 與 production rows |
| loader source guard | approved persistent source family only | production data 仍需 Owner 保證來源與 lineage 正確 |
| RLS / grant | manual template has optional sections and read-only verification | production role/policy names 仍是 Owner 決策 |
| Telegram confirmed consumption | loader only confirms approved persistent source rows and fails closed otherwise | production rows 未通過前 Telegram 不得 confirmed |

## 契約影響

- `build_market_theme_evidence_readonly_smoke(...)` 回傳結構包含 `schema_decision: "no-schema-change"`。
- `scripts/smoke_market_theme_evidence_readonly.py` CLI 輸出包含 `schema_decision: no-schema-change`。
- `load_confirmed_market_theme_evidence()` 回傳結構不變，但 confirmed 條件收緊：非 approved persistent `source_family` 會 `insufficient-data` 且 `confirmed=false`。
- DB schema 未改。
- Telegram payload、message list、formatter header、VERSION 未改。
- 策略 decision、BUY/SELL/RR/加減碼/停損停利門檻未改。

## 版本同步

- 本輪不升版。
- 未修改 Telegram 使用者可見報文。
- 未修改 `core/generator.py` `VERSION`。

## 直接消費者同步

- `scripts/smoke_market_theme_evidence_readonly.py` 已同步顯示 schema_decision。
- `build_market_theme_evidence_readonly_smoke()` 只有合法 confirmed row 才會 `telegram_confirmed=true`；forbidden source row fail closed。
- `tests/test_market_theme_evidence_handoff.py` 已同步 helper return contract、CLI output contract、loader source-family guard。
- Owner handoff docs 已新增 no-schema-change assessment 與 next manual steps。
- `core/generator.py` / Telegram 無需同步，因本輪未改 formatter 或 message list。

## 自檢命令

- `arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence_handoff.py tests/test_market_theme_evidence.py -q`：31 passed, 17 warnings。
- `arch -arm64 .venv/bin/python scripts/smoke_market_theme_evidence_readonly.py`：exit 2，預期 fail-closed；輸出包含 `schema_decision: no-schema-change` 與 `telegram_confirmed: false`。
- `git diff --stat` / candidate diff review：只包含本輪 docs / smoke / helper / tests。

## 殘留風險

- 未驗證 production read-only env；需 Owner 提供 `SUPABASE_URL` 與 `SUPABASE_READONLY_KEY`。
- 未執行 production SQL、RLS/grant、manual backfill 或 live write。
- no-schema-change 只表示現有 schema 足以支援下一步 manual backfill/read-only smoke，不表示 production closure 已完成。
- production data 的真實性仍需 Owner approved source / lineage；loader 只能拒絕明顯 forbidden source family。

## Blocked / Follow-up

- 若 Owner 要進 production：先執行或回傳 read-only verification 結果，再提供 approved payload / read-only env。
- 若 production verification 發現欄位、constraint、index 與已驗 schema 不一致，才需要另開 schema-change SQL 任務。
