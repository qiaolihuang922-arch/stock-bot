# QA_REPORT:

## 測試範圍

- 任務：未持倉過熱 RR 顯示 normal_patch，QA L2。
- 驗證範圍限於未持倉 Telegram 卡片 RR 顯示 formatter 與直接 regression，不擴成 full replay / backfill / production smoke。
- 可吸收 diff：`core/generator.py`、`tests/test_generator_report.py`。

## 風險預算與停止條件

1. 過熱未持倉 `rr=0` 仍顯示 `RR 0.00（不足）`，造成手機閱讀同類卡片混用。
   - 驗證：Tech regression + QA 自訂手機順序 probe。
2. 非過熱 `rr=0` 被全域誤改成 `RR -（過熱）`。
   - 驗證：既有非過熱不足 test + helper 反證。
3. 持倉路徑被 RR blocker 新規則污染。
   - 驗證：QA 自訂持倉卡 probe。

## 關聯風險掃描

- `core/generator.py` diff 只新增 `should_show_overheat_rr_blocker()` 並在 `rr_display_text()` 前置使用。
- 未修改 `calc_rr`、`entry_blockers`、`strong_prepare_bucket`、VERSION、DB、delivery/backfill 路徑。
- `tests/test_generator_report.py` 只新增技嘉類未持倉 regression。
- 目前 `core/generator.py` 的 VERSION = `v20.4.22` 是既有狀態，diff 未變更 VERSION。

## 跨區塊語意一致性

- TASK / CHANGELOG / diff 一致：
  - 目標：未持倉過熱降溫 `rr=0` 顯示 `RR -（過熱）`。
  - 非目標：不改策略 decision、calc_rr、DB、持倉狀態、live Telegram、VERSION。
  - 驗收：保留非過熱 `rr=0` 的 `RR 0.00（不足）`。

## 使用者誤讀風險

- 按手機閱讀順序補驗：
  - 卡片標題：【技嘉 2376】👀 可準備｜過熱降溫
  - 買點：不可買，待降溫後重評
  - 數據：RR -（過熱）
  - 同一卡片不含 `RR 0.00（不足）`
- 無可買 / 推薦式文案未被新增；本輪未改 summary 或分組排序。

## 質疑與反證

- Targeted pytest：
  - `tests/test_generator_report.py -k 'rr_zero_display_marks_insufficient_when_not_hidden or unheld_overheat_prepare_rr_zero_uses_overheat_blocker'`
  - Result：2 passed, 95 deselected。
- QA 補充反證：
  - 未持倉過熱 `rr=0`：`rr_display_text(..., holding=False)` 回傳 `-（過熱）`。
  - 未持倉非過熱 `rr=0`：仍回傳 `0.00（不足）`。
  - 持倉卡仍顯示 `新倉 RR：不適用（既有持倉）`，且不出現 `RR -（過熱）`。

## 未測項目

- 未跑 full `tests/test_generator_report.py`；Tech 已宣告跑過，本輪 QA 依 L2 風險預算只重跑目標 regression 並補手機順序 / 持倉反證。
- 未做 production read-only smoke、replay、backfill、live Telegram。
- 未重整其他 blocker reason 的 RR 優先序。

## QA 結論

通過
