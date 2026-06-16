# QA_REPORT: rebound_retest_source_gate_v21_1_20260616

## 測試範圍

- 未持倉突破距離門檻。
- 多日反彈修復 / 等回測文案。
- source-only 缺失的 funnel 與報文。
- 策略樣本 source-error 的 fail-closed 顯示。
- official generator dry-run 使用者可見報文。

## 關聯風險掃描

- 風險 1: 只改文案，策略仍淘汰。
  - 反證: `unheld_funnel_state` regression 要求 source-only 缺失回 `等資料`，非 `淘汰`。
- 風險 2: 連漲修復被直接放寬成可買。
  - 反證: dry-run 仍顯示 `等回測`，不是 `可買`。
- 風險 3: 急彈追價被誤用最近支撐回測。
  - 反證: `tests/test_unheld_gap_format.py` 保留急彈待回測的前高/突破區分支。
- 風險 4: source-error 還顯示可用風險報酬。
  - 反證: source-error regression 不允許 `數據：風險報酬 2.1`。

## 跨區塊語意一致性

- `<=5%` 接近突破契約與 `can_buy` 距離拒絕一致。
- source 缺失的 title、進場、缺口、可買條件都指向補資料，不再混成策略淘汰。
- 多日修復回測條件和可買條件都以「最近修復支撐不破」描述。
- summary 只列追蹤，不新增可買。

## 使用者誤讀風險

- `等回測` 仍可能被誤讀成「快可買」；本輪用 `進場：不買` 與 `可買：回測不破 + 非追高 + 量能有效` 限定。
- source 缺失仍可能看起來像資料壞；這是正確 fail-closed，不用 RR 數字掩蓋。

## 失敗標本反證

- Owner 樣本 1: 聯電 source 缺失 / 接近區卻顯示 `淘汰`。
  - 反證: official dry-run 顯示 `【聯電 2303】⏳ 等資料｜策略樣本證據不足`。
- Owner 樣本 2: 旺宏連漲修復仍淘汰。
  - 反證: official dry-run 顯示 `【旺宏 2337】⏳ 等回測｜反彈修復待回測`。
- Owner 樣本 3: 群創連漲修復仍淘汰。
  - 反證: official dry-run 顯示 `【群創 3481】⏳ 等回測｜反彈修復待回測`。

## 質疑與反證

- 質疑: 是否用假多日資料？
  - 反證: 最近支撐只讀 `cross_day_context.recent_daily_price_points` 中 `source=daily_price` 的 close；沒有資料時只顯示泛稱，不補價。
- 質疑: 是否不符合常規？
  - 反證: 外部對照確認突破買區、量能確認、回測支撐與風險報酬是常見交易檢查；本輪未新增裸追高。
- 質疑: 是否只是刪文案？
  - 反證: 修改包含 `can_buy`、`unheld_funnel_state`、entry contract、RR display 和 tests。

## 未測項目

- 未做 live Telegram delivery。
- 未跑 GitHub runner artifact。
- 未做 DB write/backfill/prune。
- 未驗 production scheduled artifact。

## QA 結論

通過。
