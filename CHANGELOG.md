# CHANGELOG: holding_card_contract_v21_1_20260616

## 修改內容與檔案

- `presentation/report.py`
  - 新增 `_holding_action_contract`，把持倉卡收斂成 `決策 / 缺口 / 可續抱或再進場 / 下一步`。
  - 持倉卡移除可見噪音：`交易狀態`、`數據`、`回測`、`歷史`。
  - 停損、減碼、停利、洗盤續抱、新倉風控觀察分別保留不同後續條件。
  - execution memory 不足時保留 fail closed 文案，不輸出停利股數。
  - 新插入的 contract lines 會套用盤中/盤後語境轉換，避免盤後出現 `盤中先觀察`。
- `tests/test_generator_report.py`
  - 更新持倉卡片驗收，改驗新契約與舊噪音不再出現。

## 契約影響

- message list:
  - 持倉卡從長格式改為手機閱讀格式。
  - 主行動仍為 `決策`，避免弱化停損/減碼/續抱訊號。
  - `條件` 改為 `缺口`，語意與未持倉卡一致。
- 函式回傳:
  - 無 public API shape 變更。
- DB:
  - 無 schema change。
  - 無 write/backfill。
- CLI/runner:
  - 無 live Telegram delivery。

## 版本同步

- Runtime 報文版本維持 `v21.1`。

## 直接消費者同步

- `generate_report(dry_run=True)` 已驗 official message list。
- `formatTelegramPositionCard` 相關 generator tests 已驗。

## 未影響模組

- `services.analysis` 未改。
- `core.trade_state_machine` 未改。
- DB writer/backfill 未改。
- 未持倉策略判斷未改。

## 自檢命令與結果

- `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -q --tb=short`
  - `203 passed, 44 subtests passed`
- `.\.venv\Scripts\python.exe -m pytest -q --tb=short`
  - `479 passed, 8 skipped, 108 subtests passed`
- dry-run:
  - `generate_report(dry_run=True)`
  - 持倉卡已顯示 `決策 / 缺口 / 可續抱或再進場 / 下一步`
  - 持倉卡未顯示 `交易狀態 / 數據 / 回測 / 歷史`

## 覆蓋層級

- formatter: covered。
- official generator: covered。
- runner production artifact: 未 live delivery；需等下次 scheduled bot artifact 觀察。

## 殘留風險

- 若 production artifact 仍顯示舊長格式，優先查 runner 使用的 commit / deployment path，而不是再改 formatter。
