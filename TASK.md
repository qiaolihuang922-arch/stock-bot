# TASK: strategy_buy_path_db_replay_audit_v21_1_20260616

## 任務狀態

- task_id: `strategy_buy_path_db_replay_audit_v21_1_20260616`
- 任務類型: `risk_patch`
- 狀態: `implemented + targeted replay passed`
- 版本建議: 報文 header 維持 `v21.1`
- QA 分級: L2

## Owner 問題

Owner 要確認目前策略是不是被 `等回測 / 等冷卻 / 等接近 / 等量能 / RR / 品質` 等 gate 卡死，導致真實股市裡永遠沒有可買或加碼時機。

核心問題：

- `待回測` 後是否必然變可買？
- 會不會又進入下一個 `跌太多不買 / 量能不足 / 品質不足`？
- 目前策略是否真的能在歷史真實資料中產生可買案例？

## 使用者可見結果

- 新增 read-only DB replay artifact：
  - `reports/audit/strategy_buy_path_replay_v21_1_20260616.json`
- artifact 會列出：
  - 兩年 watchlist stock-day 狀態統計。
  - `等回測` 下一個狀態分布。
  - `可買 / 趨勢延續 / 可準備` 是否真的存在。
  - snapshot 原始可交易訊號是否被 funnel 錯擋。

## 非目標

- 不修改正式策略門檻。
- 不修改 Telegram 報文。
- 不寫 DB / 不回寫 / 不去重。
- 不做 live Telegram delivery。
- 不新增 DB schema。

## 影響模組與直接消費者

- `scripts/audit_strategy_buy_path_replay.py`
  - read-only DB replay 工具。
- `tests/test_strategy_buy_path_replay.py`
  - replay artifact 結構與 transition 統計測試。
- 直接消費者:
  - Architect / Owner 讀 replay artifact 判斷策略是否 deadlock。

## 輸出契約

Artifact 必須包含：

- `read_only: true`
- `db_write: false`
- `schema_change: false`
- `live_telegram: false`
- `totals`
- `state_counts`
- `primary_blocker_counts`
- `wait_retest_next_state`
- `diagnosis`
- `first_buy_like_examples`
- `first_snapshot_tradeable_blocked_examples`

## 驗收條件

- Replay 從 Supabase `daily_price` read-only 讀取，不寫 DB。
- 產出 artifact 且包含 12 檔 coverage。
- 能回答是否有 deadlock：
  - `diagnosis.deadlock_suspected`
  - `diagnosis.has_real_buyable_path`
  - `diagnosis.funnel_blocks_snapshot_tradeable`
- Targeted tests 通過。
- Full pytest 通過後才能 commit/push。

## 失敗標本與驗收路由

- 失敗標本:
  - Owner 質疑「連續十幾天都沒有可買點 / 待回測後是否永遠下一個 gate」。
- 驗收路由:
  - DB read-only replay artifact。
  - `tests/test_strategy_buy_path_replay.py`。

## 禁止事項與阻塞條件

- 禁止使用 synthetic fixture 代替 production DB replay 結論。
- 禁止把 dry-run 成功升格成策略有效；必須看 artifact 統計。
- 禁止 DB write / schema change / live Telegram。
