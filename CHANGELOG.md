# CHANGELOG: strategy_soft_gate_patch_v21_1_20260616

## 修改內容與檔案

- `presentation/report.py`
  - 持倉卡片改成一個主決策 + 一個 `明日處理`，移除同一卡內的 `缺口 / 可恢復 / 下一步` 重複。
  - `等冷卻` 改成 `狀態` + `等待`，把熱度降溫條件合併成有效買點，不再顯示一般 `進場 / 缺口 / 可買`。
  - `等回測` 改成 `狀態` + `回測` + `有效買點`，並避免在回測 anchor 和有效買點內重複同一價格。
  - `等型態` 改成 `狀態` + `等待` + `有效買點`，避免把 setup/quality 未成立寫成資料缺口。
  - `等接近` 保留突破區與距離，但只顯示一次突破區。
- `tests/test_generator_report.py`
  - 更新持倉、冷卻、回測、型態、接近狀態的 mobile card assertions。
- `tests/test_trade_state_machine.py`
  - 同步 `等接近` mobile-readable card contract。

## 契約影響

- 報文版本仍為 `v21.1`。
- Telegram message list shape 不變，單一卡片內的行文契約改為 state-specific。
- 策略 gate / RR / volume / DB replay calculation 不變。
- DB:
  - no schema change。
  - no write/backfill/prune。
- Telegram:
  - no live delivery。

## 未影響模組

- 不改 `core/generator.py` 策略門檻。
- 不改 DB schema。
- 不改 Render/GitHub dispatch。
- 不改 live Telegram sender。

## 自檢命令與結果

- Targeted report/state tests:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py tests\test_trade_state_machine.py -q --tb=short`
  - result: `215 passed, 155 warnings, 46 subtests passed`
- Full:
  - `.\.venv\Scripts\python.exe -m pytest -q --tb=short`
  - result: `489 passed, 8 skipped, 165 warnings, 110 subtests passed`
- Official generator dry-run:
  - `from core.generator import generate_report; generate_report(dry_run=True)`
  - result: `4` messages generated, no live Telegram.

## 覆蓋層級

- formatter: covered。
- official generator message list: covered by dry-run。
- runner artifact: equivalent dry-run path covered locally。
- production DB write: not run by design。
- live Telegram: not run by design。

## 殘留風險

- This cycle fixes mobile card semantics, not strategy thresholds.
- Further calibration still belongs to separate strategy replay tasks, especially rule outcome sub-classification.
