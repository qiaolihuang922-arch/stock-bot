# QA_REPORT: db_backed_price_transition_v21_1_20260617

## 測試範圍

- DB-backed recent price transition。
- 連漲後當日回落的未持倉分類。
- data volume ratio 與舊 `NO_VOLUME` / `volume_state=WEAK` 的衝突。
- formatter 盤面文字、數據行與 funnel state 一致性。
- Full regression suite。

## 關聯風險掃描

- 風險 1: 旺宏這類昨日漲今日跌仍顯示趨勢延續。
  - 反證: regression 驗證 DB 日線連漲 + 當前價回落時 `multi_day_rebound_needs_retest=True` 且 funnel state 為 `等回測`。
- 風險 2: 群創 V 1.18x 仍被舊欄位打成量能不足。
  - 反證: regression 驗證 data-aware result 中 `volume_ratio=1.18` 不產生 `量能不足`，卡片不出 `等量能｜量能不足` 或 `風險報酬 -（量能不足）`。
- 風險 3: 聯電連續轉弱仍顯示極強 / 不可追高。
  - 反證: formatter direct test 驗證 DB-backed continuous-down 不顯示 `極強` / `不可追高觀察`。
- 風險 4: 遠離突破股票被量能搶成主 blocker。
  - 反證: 既有遠離低位修復 regression 仍通過，遠離約 20% 的緯創維持 `等低位修復` / `等接近`，不被低量覆蓋。
- 風險 5: 修正污染原始 payload，造成同一 run 前後狀態不一致。
  - 反證: implementation 改為 local data-aware result，不回寫 `_volume_ratio_from_data` 到原 result。

## 跨區塊語意一致性

- Summary / card / data row 對聯電一致為量能未過，不再同時寫不可追高與等量。
- 旺宏卡片保留 `距突破`，但主狀態是 `等回測｜反彈修復待回測`，避免讀者誤解成趨勢延續可追。
- 群創連漲並接近突破時，主阻擋為過熱 / 漲停反彈待確認，不再被舊量能欄位誤導。

## 使用者誤讀風險

- `等回測` 不是可買，只代表要等回踩不破與非追高。
- `volume_ratio >= 1.1` 解除「量能不足」文字，不代表買點成立；仍需風險報酬、型態與熱度條件。
- 遠離區的量能不足不應成主因，因為讀者真正要等的是低位修復或重新接近有效區。

## 失敗標本反證

- Owner specimen: 06/17 盤中旺宏、群創、聯電卡片。
- Dry-run result:
  - 聯電: `等量能｜等量` with V around `0.46x`。
  - 旺宏: `等回測｜反彈修復待回測`，回測基準為最近反彈收盤。
  - 群創: `等冷卻｜漲停反彈待確認`，未顯示量能不足。
  - 緯創 / 技嘉 / 仁寶: `等低位修復`，保留支撐 / 5日均 / 量能缺口。

## 質疑與反證

- 質疑: 是否用假跨日資料？
  - 反證: transition helper 只讀 `cross_day_context.recent_daily_price_points` 且要求 source 為 `daily_price`。
- 質疑: 是否只改文字？
  - 反證: `unheld_funnel_state`、`multi_day_rebound_needs_retest`、formatter direct test、official dry-run 均覆蓋。
- 質疑: 量能門檻是否過度擴張？
  - 反證: `volume_ratio < 1.1` 只在接近區作主 blocker；遠離區 regressions 仍保留低位修復 / 等接近。

## 未測項目

- 未 live Telegram。
- 未 DB write / backfill / prune。
- 未實際 GitHub runner artifact；已用 official local dry-run equivalent 驗 message list。

## QA 結論

通過。

本輪修正把 06/17 盤中標本的跨日價格變化與量能 blocker 對齊到 DB-backed / report-backed 資料，不新增 schema、不寫 DB、不 live TG。
