# TASK: holding_card_contract_v21_1_20260616

## 任務狀態

- task_id: `holding_card_contract_v21_1_20260616`
- 任務類型: `normal_patch`
- 狀態: `QA passed, pending commit/push`
- 版本建議: 報文 header 維持 `v21.1`
- QA 分級: L2

## Owner 問題

Owner 貼出 06/16 盤中持倉報文，指出持倉卡仍塞入 `交易狀態`、`條件`、`數據`、`回測`、`歷史` 等噪音，閱讀感與已優化的未持倉卡不一致。Owner 要求上網查常規，並把持倉卡改成與未持倉同樣的決策式呈現。

## 使用者可見結果

- 持倉卡保留必要風控資料：倉位、風控、盤面、距突破、價格。
- 持倉主行動只保留一個 `決策：...｜原因：...`。
- 原 `條件` 改為 `缺口`，說明還差什麼或觸發了什麼風控。
- 補 `可續抱` / `可恢復` / `再進場`，讓使用者知道後續條件。
- 保留 `下一步`，但依盤中/盤後語境轉換。
- 不顯示持倉卡的 `交易狀態`、`數據`、`回測`、`歷史`，避免手機版重複與誤讀。
- 不做 live Telegram delivery。
- 不做 DB schema/write/backfill。

## 非目標

- 不重算買賣策略、停損線、警戒線或持倉狀態機。
- 不修改未持倉策略判斷。
- 不修改 DB。

## 影響模組與直接消費者

- `presentation/report.py`: 持倉卡片 formatter。
- `tests/test_generator_report.py`: 持倉卡片可讀性與防回退。
- 直接消費者: official `generate_report(dry_run=True)` message list、runner/bot Telegram artifact。

## 輸出契約

持倉卡順序：

1. title: `【股票】📌 主行動｜損益`
2. `倉位`
3. `風控`
4. `盤面`
5. `距突破`
6. `決策：...｜原因：...`
7. `缺口：...`
8. `可續抱` / `可恢復` / `再進場`
9. `下一步`
10. `價格`

不得在持倉卡顯示 `交易狀態：`、`數據：`、`回測：`、`歷史：`。

## 驗收條件

- official dry-run 的持倉卡不再顯示 `交易狀態`、`數據`、`回測`、`歷史`。
- 停損卡仍明確顯示停損決策、原因、再進場條件與下一步。
- 續抱/洗盤/新倉風控觀察卡仍明確顯示不加碼與風控缺口。
- full pytest 通過。

## 失敗標本與驗收路由

- 失敗標本: Owner 貼出的 06/16 盤中持倉報文。
- 驗收路由:
  - formatter: `tests/test_generator_report.py`
  - official dry-run: `generate_report(dry_run=True)`

## 禁止事項與阻塞條件

- 禁止 live Telegram delivery。
- 禁止手寫 production DML。
- 若 production runner artifact 與 dry-run 不一致，下一輪必須先查 runner commit / deployment path。
