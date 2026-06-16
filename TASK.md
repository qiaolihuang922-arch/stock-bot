# TASK: strategy_soft_gate_patch_v21_1_20260616

## 任務狀態

- task_id: `strategy_soft_gate_patch_v21_1_20260616`
- 任務類型: `risk_patch`
- 狀態: `implemented`
- 版本建議: 報文 header 維持 `v21.1`
- QA 分級: L3

## Owner 問題

Owner 指出 DB replay 後仍有策略與報文可讀性問題：

- 漲停 / 過熱 / 連漲後不應永遠不能買，已由 soft-gate replay 修正。
- `等接近`、`等回測`、`等型態` 的手機卡片不應把同一件事拆成 `進場 / 缺口 / 可買 / 明日觸發` 重複說。
- 持倉卡片不應同時顯示 `缺口 / 可恢復 / 下一步`，因為 Owner 要的是明日怎麼處理。
- 修正必須沿 official generator / runner 報文路徑驗證，不得只改 helper fixture。

## 使用者可見結果

- 持倉卡片只保留:
  - `決策：...｜原因：...`
  - `明日處理：...`
- 未持倉依狀態顯示:
  - `等冷卻`: `狀態` + `等待`
  - `等回測`: `狀態` + `回測` + `有效買點`
  - `等型態`: `狀態` + `等待` + `有效買點`
  - `等接近`: `進場` + `等待`
- `距突破` 保留，因為它是 Owner 要看的固定定位資訊。

## 非目標

- 不做 live Telegram delivery。
- 不寫 DB / 不回寫 / 不去重。
- 不新增 DB schema。
- 不改策略門檻或回測資料。
- 不承諾任何單一標的必買。

## 影響模組與直接消費者

- `presentation/report.py`
  - Telegram card formatter。
- `tests/test_generator_report.py`
  - 使用者可見報文與 regression。
- 直接消費者:
  - official generator message list。
  - dry-run / runner artifact。
  - Telegram mobile reader。

## 輸出契約

- 不同 funnel state 不能共用同一套重複文案。
- `等冷卻` 不顯示一般 `進場 / 缺口 / 可買` 三行。
- `等回測` 必須明確說回測哪個 anchor，且 `有效買點` 不重複同一 anchor。
- `等型態` 必須說明等待的 setup / quality 條件，不把它寫成資料缺口。
- `等接近` 必須保留突破區與距離，但不能重複同一突破區三次。
- 持倉同一股票同一報文只能有一個主行動與一個明日處理。

## 驗收條件

- Generator report + trade state tests 通過。
- Full pytest 通過。
- Official generator dry-run 顯示:
  - holdings 使用 `明日處理`。
  - cold / retest / setup / near-trigger cards 使用各自模板。
- 不做 DB write / schema change / live TG。

## 失敗標本與驗收路由

- 失敗標本:
  - Owner 貼出的 `06/16` 報文中，`等接近` 和 `等回測` 同一條件被多行重複。
  - Owner 截圖顯示手機閱讀時單一卡片過長且語意重複。
- 驗收路由:
  - `tests/test_generator_report.py`
  - `tests/test_trade_state_machine.py`
  - official `generate_report(dry_run=True)` message list。

## 禁止事項與阻塞條件

- 禁止只做文字替換而不按 state 分流。
- 禁止刪除 Owner 指定要保留的 `距突破`。
- 禁止用對話記憶或假跨日資料。
- 禁止 live Telegram。
- 禁止手寫 production DML。
