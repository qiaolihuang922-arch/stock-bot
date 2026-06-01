# QA_REPORT:

## 測試範圍

- 任務：`evidence-chain-maturity-100`
- 任務尺寸 / QA：`risk_patch / L3`
- 驗證範圍：五維 evidence maturity verifier、production-readonly artifact proof、handoff gate、Telegram v20.4.19 三則順序與 evidence 可讀性。
- 未擴成 full pytest、正式 replay、backfill、live Telegram 或 production write。

## 關聯風險掃描

- `production_all_sources_available`：exit 0，`maturity_score=100`，五維皆 `{score:100,status:pass}`，`blocking_findings=[]`。
- `strategy_sample_synthetic_only`：exit 2，`strategy_sample_evidence` blocked。
- `runner_stale_artifact_blocked`：exit 2，`repeatable_runner_process` blocked。
- `ledger_position_conflict`：exit 0，ledger artifact 保留 `status=unresolved-conflict`、`conflict=position-vs-events`。
- strategy / ledger production-readonly artifact 均包含 `source_artifact_exists=true` 與 `source_artifact_sha256`，QA 已比對實際 hash。
- diff 掃描未見 DB schema/migration、production DML/write path、live Telegram send path 變更。

## 跨區塊語意一致性

- TASK / CHANGELOG / diff 一致：版本 `v20.4.19`、五維 maturity、read-only flags、synthetic/stale fail closed、ledger conflict fail closed。
- Telegram message order 維持：messages[0] 持倉、messages[1] 未持倉、messages[2] evidence。
- 第三則 evidence 保留 source/status/use/limit/conflict 並維持人話可讀。
- Handoff gate 可重跑，會檢查 artifact type/version/score、五維 dimensions、telegram_messages、artifacts、source proof/hash、safety flags、repo/worktree binding。

## 使用者誤讀風險

- `maturity_score=100` 代表 evidence chain 可追溯、缺資料與衝突會被揭露並 fail closed；不代表策略樣本 source 本身已可用，也不代表 ledger conflict 已修復。
- `production_all_sources_available` case 中 strategy sample 仍可能是 `missing-source`，但會以 production-readonly source artifact 明確揭露並顯示「不納入買賣判斷」。
- ledger conflict case 未輸出「已確認停利 / 可賣股數 / 有效執行結論」。

## 質疑與反證

- forged minimal 100 artifact 被 `check_evidence_handoff_gate.sh` 擋下。
- 移除 production source hash 的 artifact 被 gate 擋下。
- 舊 repo/worktree binding artifact 被 gate 擋下。
- synthetic-only strategy sample 被 maturity CLI 以 exit 2 擋下。
- stale runner artifact 被 maturity CLI 以 exit 2 擋下。

## 未測項目

- 未做 live Supabase write、production DML、backfill、live Telegram delivery。
- 未處理 Telegram reply markup 附著最後一則 message 的旁支風險。
- 未修 2356 / ledger production 資料本身；本輪只完成 maturity evidence chain 與 fail-closed gate。

## QA 結論

通過
