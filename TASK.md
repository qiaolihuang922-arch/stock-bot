# TASK: db_backed_price_transition_v21_1_20260617

## 任務狀態

- task_id: `db_backed_price_transition_v21_1_20260617`
- 任務類型: `risk_patch`
- 狀態: `implemented`
- 版本建議: 報文 header 維持 `v21.1`
- QA 分級: L3

## Owner 問題

Owner 指出 06/17 盤中報文中，多檔股票的本週價格變化與策略狀態不一致：旺宏昨日漲今日跌卻顯示趨勢延續，群創連漲且 V 1.18x 卻仍像量能不足，聯電連續轉弱卻顯示過強 / 不可追高。Owner 要求用 DB 真實跨日資料修正，不得用假記憶。

## 使用者可見結果

- 旺宏這類 DB 顯示連漲後當日回落的標的，改判為 `等回測｜反彈修復待回測`，不再顯示趨勢延續。
- 群創這類量比已修復到有效區間的標的，不再被 `NO_VOLUME` 舊欄位硬打成 `等量能｜量能不足`。
- 聯電這類接近區但量比不足的標的，改回 `等量能`，不再包成 `不可追高觀察｜等量`。
- 遠離 20% 以上的標的仍優先顯示低位修復 / 等接近，不讓量能搶成主 blocker。

## 非目標

- 不做 live Telegram delivery。
- 不寫 DB / 不回寫 / 不去重。
- 不新增 DB schema。
- 不把回測 / 低位修復直接升成可買。
- 不改持倉 hard-stop / 減碼風控規則。

## 影響模組與直接消費者

- `core/generator.py`: DB-backed recent price transition、data-aware volume gate、未持倉 funnel state。
- `presentation/report.py`: data-aware volume / distance result merge、盤面文字防衝突。
- `tests/test_generator_report.py`: Owner 失敗標本回歸。
- 直接消費者: official generator message list、dry-run / runner artifact、Telegram mobile reader。

## 輸出契約

- 跨日趨勢 / 回測判斷只能使用 `cross_day_context.recent_daily_price_points` 中 `source=daily_price` 的 DB 日線收盤，並用當前 `price` 判斷當日變化。
- `UP_THEN_DOWN` 且前段連漲修復成立時，狀態應進 `等回測`，不是趨勢延續。
- `volume_ratio >= 1.1` 且來自 data/report payload 時，不得再顯示 `量能不足`。
- `volume_ratio < 1.1` 只有在接近買點區（約 8% 內）才作主 blocker；遠離區仍看低位修復 / 等接近。
- formatter 不得用未合併 data 量比的舊 result 產生與核心狀態衝突的數據行。

## 驗收條件

- Unit/report tests 覆蓋旺宏、群創、聯電三個 Owner failure pattern。
- Full pytest 通過。
- Official generator dry-run 顯示:
  - 旺宏: `等回測｜反彈修復待回測`。
  - 群創: 不再 `等量能｜量能不足`。
  - 聯電: 低量時為 `等量能`。
  - 低位修復卡仍保留支撐 / 5日均 / 量能缺口。
- 不做 DB write / schema change / live TG。

## 失敗標本與驗收路由

- 失敗標本:
  - Owner 貼出的 06/17 盤中未持倉卡：旺宏、群創、聯電。
- 驗收路由:
  - `core.generator.recent_price_transition`
  - `core.generator.multi_day_rebound_needs_retest`
  - `core.generator.unheld_funnel_state`
  - `presentation.report.formatTelegramUnheldCard`
  - official `generate_report(dry_run=True)` message list。

## 禁止事項與阻塞條件

- 禁止用 runtime dict / 對話記憶模擬跨日。
- 禁止 DB 缺資料時宣稱連漲 / 回測。
- 禁止用單一舊欄位覆蓋已知有效的 data volume ratio。
- 禁止 live Telegram。
- 禁止手寫 production DML。
