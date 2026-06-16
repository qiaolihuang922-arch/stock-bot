# QA_REPORT: dry_run_strategy_evidence_near_breakout_v21_1_20260616

## 測試範圍

- 本地 dry-run strategy evidence read-only 路徑。
- 接近突破 C 品質追蹤態。
- official unheld message。
- summary 未持倉狀態。

## 關聯風險掃描

- 風險 1: dry-run 讀 DB 變成寫 DB。
  - 反證: 修改只在 dry-run 呼叫 `load_strategy_evidence_summary`，沒有呼叫 `record_*`。
- 風險 2: 接近突破 C 品質被升格成可買。
  - 反證: dry-run 聯電顯示 `等型態｜觀察`，不是 `可買`。
- 風險 3: source 真缺失時被誤放行。
  - 反證: source missing regression 仍保留 fail-closed。

## 跨區塊語意一致性

- 聯電卡片不再說缺資料；summary 也不再把聯電列為淘汰。
- `距突破：4.06%｜接近突破` 與追蹤態一致。
- 報文仍明確說 `進場：不買`，避免誤讀成有效進場。

## 使用者誤讀風險

- `等型態｜觀察` 代表接近但買點品質未過，不是買入。
- dry-run 現在會讀 production strategy evidence，因此本地測試結果更接近 bot artifact，但仍不是 live Telegram。

## 失敗標本反證

- 原失敗: 聯電顯示 `等資料｜策略樣本證據不足`。
  - 反證: dry-run 修復後不再顯示 `等資料`。
- 二次失敗: 聯電資料恢復後顯示 `淘汰｜觀察`。
  - 反證: dry-run 修復後顯示 `等型態｜觀察`。

## 質疑與反證

- 質疑: 聯電是不是缺行情資料？
  - 反證: dry-run 讀取 strategy evidence 後，聯電價格、距突破與狀態均正常；缺的是 dry-run 原先跳過全域 strategy evidence。
- 質疑: 是否用假資料？
  - 反證: 讀取使用既有 `load_strategy_evidence_summary` 和 Supabase client；失敗時 fail closed。

## 未測項目

- 未做 live Telegram delivery。
- 未跑 GitHub runner artifact。
- 未做 DB write/backfill/prune。

## QA 結論

通過。
