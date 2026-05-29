# RESEARCH.md

本文件保存最新研究任務的高信號摘要，不保留完整聊天紀錄。

## Latest Research

- task_id: `db_end_to_end_usage_audit_20260529`
- 日期：2026-05-29
- 狀態：已由 Architect 吸收；後續已進入 Phase 1 開發
- 研究性質：只讀審計，不改 code、不寫 DB、不 live Telegram

## Question

Owner 問題：既然 DB 已經有多表資料，策略是不是其實沒有用到？需要從頭到尾檢查 DB 取值 / 存值 / 策略消費鏈路，區分：

- 已入庫且會進 live strategy decision。
- 已入庫但只進 Telegram / report / evidence / audit。
- 已入庫但 runtime 未消費。
- 策略仍使用即時行情 / Yahoo / runtime calculation 而不是 DB 的路徑。

## Findings

### 已進 live 策略 / 報文決策的 DB 資料

- `positions`：持倉 source-of-truth。`v20.3.1` 後缺來源時 fail closed，不回全 watchlist 0 股。
- `position_events`：今日 / 歷史執行事件 source-of-truth。`v20.3.1` 後 source-error / missing-source 不回 fake 0 event；`v20.4.0` 開始用於同級停利 / 減碼 / 今日買入 guard。

### 已入庫但 Phase 1 前主要未進核心買賣門檻

- `daily_signal_snapshot`
- `signal_runs`
- `signal_items`
- `signal_outcomes`
- `strategy_feature_snapshots`
- `strategy_outcome_metrics`
- `strategy_classification_audit`
- `market_daily_bars`

結論：這些資料不是「白做」，但原本多數定位是 snapshot / evidence / audit / replay / report，不應未定義就硬塞進 BUY / SELL 門檻。

### 策略仍主要使用 runtime 計算的資料

- 價格、OHLCV、均線、量能、突破、score：主要由 `services/stock_api.py`、Yahoo / TWSE / realtime path 與 `services/analysis.py` runtime 計算。
- Telegram formatter：`core/generator.py` 消費 strategy result、holding、position events、evidence summary，輸出 Owner 手機報文。

## Product Conclusion

- DB 不是直接替代即時策略引擎，而應先承擔「記憶」與「證據權重」。
- Phase 1 正確方向：用 DB 影響排序、summary、準備層、歷史追溯、同級行動去重；不得單獨把不可買改成可買。
- 若要進一步讓 DB 影響核心 strategy decision，需要 Phase 2 任務明確定義 source precedence、欄位 mapping、production schema 與 QA L3 範圍。

## Follow-up

- Phase 1 已進開發：`DB Strategy Consumption Phase 1 - Cross-day State And Evidence Weight`。
- Phase 2 可選方向：
  - 接入 `signal_runs / signal_items / signal_outcomes` 的真實 signal history。
  - 將 `strategy_classification_audit` 轉成 previous classification / audit severity context。
  - 建立 production DB schema mapping 驗證，不做 live write。
