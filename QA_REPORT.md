# QA_REPORT: entry_quality_priority_v21_1_20260616

## 測試範圍

- 未持倉策略主因排序。
- `entry_quality D` / `market_grade D` 不再單獨搶主因。
- Telegram 未持倉卡片手機閱讀路徑。
- official generator dry-run。

## 關聯風險掃描

- 持倉主行動未改。
- live Telegram 未執行。
- DB schema/write/backfill 未執行。
- 版本 header 維持 `v21.1`。

## 跨區塊語意一致性

- 未持倉 title、進場、缺口、可買、觀察均使用同一主因排序。
- `距突破` 保留獨立顯示，但不覆蓋急彈/漲停/過熱/RR。
- 品質 D 只在缺型態時顯示，不再覆蓋具體 blocker。

## 使用者誤讀風險

- 已降低「永遠 D、永遠個股弱勢」誤讀。
- `等接近` 仍不是買進訊號；報文明確顯示 `進場：不買`。
- `策略樣本不足` 仍可能出現，代表 source fail-closed，不可改成假資料。

## 失敗標本反證

- Owner 06/16 盤前未持倉報文等價 dry-run:
  - 華邦電: `等回測｜漲停不追`
  - 南亞科: `等冷卻｜過熱觀察`
  - 聯電: `等風險報酬｜觀察`
  - 緯創/仁寶/技嘉: `等接近｜遠離觸發`
  - 旺宏: `等回測｜急彈待回測`
  - 群創: `淘汰｜弱反彈待確認`

## 質疑與反證

- 質疑: 是否只是硬改文字？
  - 反證: 修改 `entry_setup_state`、state machine guard、generator blocker ordering、presentation fallback，多層均同步。
- 質疑: 是否把距離變成死規則？
  - 反證: 急彈/漲停/過熱/RR 優先於距離；旺宏仍是等回測，不被距離覆蓋。
- 質疑: 是否產生假資料？
  - 反證: 沒有新增 DB 欄位、沒有回寫、沒有 synthetic cross-day memory。

## 未測項目

- 未送 live Telegram。
- 未驗 GitHub scheduled runner 實際 artifact；需等下次 `run_mode=bot`。

## QA 結論

通過。
