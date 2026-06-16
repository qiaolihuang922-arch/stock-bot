# TASK: db_backed_low_repair_v21_1_20260616

## 任務狀態

- task_id: `db_backed_low_repair_v21_1_20260616`
- 任務類型: `risk_patch`
- 狀態: `implemented`
- 版本建議: 報文 header 維持 `v21.1`
- QA 分級: L3

## Owner 問題

Owner 指出遠離突破的股票被報文寫成只能「等接近突破區」，等於要求價格回到前高附近才可能買，策略過於僵硬。Owner 要求確認 DB 是否支援真正跨日判斷；若支援就直接改，不得用對話記憶或假資料。

## 使用者可見結果

- DB 有 `daily_price` 跨日 OHLCV 時，遠離突破但具備 pullback/reclaim 類型的未持倉標的，不再只顯示 `等接近`。
- 新增使用者可見狀態: `等低位修復｜低位修復觀察`。
- 低位修復卡片顯示:
  - `路線：突破買點太遠，改看低位修復`
  - `觀察：近期支撐 ...；5日均 ...；量能 ...x`
  - `有效買點：近期支撐不破 + 站回5日均 + 量能轉強 + 風險報酬 >= 1.5`
- 無 DB 日線或 DB 日線不足時仍 fail closed，不顯示低位修復。

## 非目標

- 不做 live Telegram delivery。
- 不寫 DB / 不回寫 / 不去重。
- 不新增 DB schema。
- 不把低位修復直接升成可買。
- 不承諾任何單一標的必買。

## 影響模組與直接消費者

- `services/cross_day_context.py`: 讀取並保留 `daily_price` 的 open/high/low/close/volume。
- `core/generator.py`: 新增 DB-backed `等低位修復` funnel state。
- `core/trade_state_machine.py`: 同步 `WAIT_LOW_REPAIR` 狀態。
- `presentation/report.py`: 新增低位修復卡片契約。
- 直接消費者: official generator message list、dry-run / runner artifact、Telegram mobile reader。

## 輸出契約

- `距突破` 必須保留。
- `等接近` 只用在沒有 DB-backed 低位修復依據，或確實只剩突破接近路線時。
- `等低位修復` 必須來自 `cross_day_context.source_of_truth` 包含 `daily_price` 且至少有 4 筆日線點。
- 低位修復只代表觀察路線，不是買入訊號；有效買點仍需支撐不破、站回短均、量能轉強與風險報酬達標。

## 驗收條件

- DB read probe 證明候選標的有 `daily_price` OHLCV。
- Targeted report/state/cross-day tests 通過。
- Full pytest 通過。
- Official generator dry-run 顯示仁寶 / 緯創 / 技嘉改為 `等低位修復`，不再寫只能等接近突破區。
- 不做 DB write / schema change / live TG。

## 失敗標本與驗收路由

- 失敗標本:
  - Owner 貼出的 `仁寶 / 緯創 / 技嘉` 遠離突破卡片: `進場：不買｜尚未接近突破區 ...`。
- 驗收路由:
  - `services.cross_day_context.build_cross_day_contexts`
  - `core.generator.unheld_funnel_state`
  - `presentation.report.formatTelegramUnheldCard`
  - official `generate_report(dry_run=True)` message list。

## 禁止事項與阻塞條件

- 禁止用 runtime dict / 對話記憶模擬跨日。
- 禁止 DB 缺資料時顯示低位修復。
- 禁止把 `等低位修復` 當成直接可買。
- 禁止 live Telegram。
- 禁止手寫 production DML。
