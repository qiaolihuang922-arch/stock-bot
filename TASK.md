# TASK: dry_run_strategy_evidence_near_breakout_v21_1_20260616

## 任務狀態

- task_id: `dry_run_strategy_evidence_near_breakout_v21_1_20260616`
- 任務類型: `risk_patch`
- 狀態: `implemented + full pytest passed + pushed`
- 版本建議: 報文 header 維持 `v21.1`
- QA 分級: L2

## Owner 問題

Owner 質疑「聯電怎麼可能會缺數據」。實際根因有兩層：

- 聯電行情 / 價格 / 財報不是缺資料。
- 本地 `generate_report(dry_run=True)` 為了不寫 DB，直接跳過了 read-only `load_strategy_evidence_summary`，導致全域 strategy evidence 被標成 missing。
- 補回 read-only strategy evidence 後，聯電又露出接近突破 C 品質追蹤態掉到 `淘汰｜觀察` 的狀態機漏洞。

## 使用者可見結果

- 本地 dry-run 仍不寫 DB、不 live Telegram，但會 read-only 載入 strategy evidence。
- 聯電在資料可用時不再顯示 `等資料｜策略樣本證據不足`。
- 聯電 `距突破 4.06%｜接近突破` + 買點品質 C 不再顯示 `⛔ 淘汰`；改為追蹤態，例如 `等型態｜觀察`。
- summary 不再把聯電列入淘汰。

## 非目標

- 不新增買點或加碼訊號。
- 不做 live Telegram delivery。
- 不做 DB schema/write/backfill/prune。
- 不修改持倉風控核心。

## 影響模組與直接消費者

- `core/generator.py`
  - `generate_report(dry_run=True)` read-only 載入 strategy evidence。
  - `unheld_funnel_assessment` 接住接近突破 C 品質追蹤態。
- `tests/test_generator_report.py`
  - near-breakout C 品質追蹤態 regression。
- 直接消費者:
  - 本地 dry-run 報文。
  - GitHub runner/bot 產出的 official message list。

## 輸出契約

- dry-run:
  - 不寫 DB。
  - 不 live delivery。
  - 可以 read-only 載入 strategy evidence，保持本地報文與 production 判斷一致。
- near-breakout:
  - `<=5%` 且 `entry_quality=C`、`market_grade` 非 D/E、非硬結構失敗時，不得掉到 `淘汰`。
  - 仍不得升格為 `可買`；只能是追蹤/等待型狀態。

## 驗收條件

- `generate_report(dry_run=True)` 的未持倉報文中，聯電不再顯示 `等資料` 或 `淘汰`。
- 聯電顯示 `距突破：4.06%｜接近突破`，狀態為追蹤態。
- summary 顯示未持倉僅追蹤，不含聯電淘汰。
- full pytest 通過。

## 失敗標本與驗收路由

- 失敗標本:
  - `【聯電 2303】⏳ 等資料｜策略樣本證據不足`
  - 修復 read-only evidence 後一度變成 `【聯電 2303】⛔ 淘汰｜觀察`
- 驗收路由:
  - `generate_report(dry_run=True)`
  - `load_strategy_evidence_summary`
  - `unheld_funnel_state`
  - official unheld message and summary。

## 禁止事項與阻塞條件

- 禁止用假資料補 strategy evidence。
- 禁止用 dry-run 寫 DB。
- 禁止 live Telegram delivery。
- source 真缺失時仍需 fail closed。
