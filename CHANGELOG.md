# CHANGELOG: strategy_soft_gate_patch_v21_1_20260616

## 修改內容與檔案

- `core/generator.py`
  - `LIMIT_REBOUND` / `漲停反彈待確認` 從硬追高 blocker 拆出，改為隔日確認 / 回測承接。
  - HOT / EXTENDED 不再一律視為硬過熱；只有 EXTREME / AVOID / LIMIT_LOCK / RR<1.0 保持硬擋。
  - 新增 soft-gate candidate 判斷：需要 RR>=1.0、距離合理、品質可接受、量能不弱。
  - confirmed/supporting evidence 可以把軟阻擋推到 `可準備`，但不會直接推到 `可買`。
  - source-only missing 不再把漲停反彈誤改成 `等資料`。
- `presentation/report.py`
  - HOT / EXTENDED / LIMIT_REBOUND 不再預設顯示成 evidence unavailable。
  - `可準備` 顯示保留 score/evidence，不再全部變成不適用。
  - `等接近` card de-duplicates entry/gap/unlock/trigger:
    - removes repeated `可買：接近突破區...` line for far-from-trigger cards.
    - uses `等待：距突破...；有效買點只看：接近突破區 / 回測承接型態`.
    - trigger no longer repeats the exact breakout zone.
- `tests/test_generator_report.py`
  - 更新 soft-gate 報文契約。
  - 補 HOT evidence、低 RR、漲停反彈、summary funnel regression。
- `tests/test_trade_state_machine.py`
  - 同步 `等接近` mobile-readable card contract。
- Audit artifacts:
  - `reports/audit/strategy_buy_path_replay_v21_1_soft_gates_20260616.json`
  - `reports/audit/strategy_rule_outcomes_v21_1_soft_gates_20260616.json`

## 契約影響

- 報文版本仍為 `v21.1`。
- 使用者可見 funnel 可能增加 `可準備`，減少把 HOT / LIMIT_REBOUND 直接打成硬不可行動。
- `可準備` 仍不是下單訊號。
- DB:
  - read-only replay only。
  - 無 schema change。
  - 無 write/backfill/prune。
- Telegram:
  - 未 live delivery。

## 未影響模組

- 不改 DB schema。
- 不改 Render/GitHub dispatch。
- 不改 holdings position source。
- 不改 live Telegram sender。

## 自檢命令與結果

- Generator report:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -q --tb=short`
  - result: `206 passed, 153 warnings, 46 subtests passed`
- Full:
  - `.\.venv\Scripts\python.exe -m pytest -q --tb=short`
  - result: `489 passed, 8 skipped, 165 warnings, 110 subtests passed`
- Official generator dry-run:
  - `from core.generator import generate_report; generate_report(dry_run=True)`
  - result: `4` messages generated, no live Telegram.
- DB buy-path replay:
  - `.\.venv\Scripts\python.exe scripts\audit_strategy_buy_path_replay.py --lookback-days 730 --version v21.1 --output reports\audit\strategy_buy_path_replay_v21_1_soft_gates_20260616.json`
  - result:
    - `deadlock_suspected=false`
    - `has_real_buyable_path=true`
    - `has_prepare_path=true`
    - `snapshot_tradeable_blocked_by_funnel_days=0`
    - `可買 700`
    - `可準備 364`
- DB rule outcome replay:
  - `.\.venv\Scripts\python.exe scripts\audit_strategy_rule_outcomes.py --lookback-days 730 --version v21.1 --output reports\audit\strategy_rule_outcomes_v21_1_soft_gates_20260616.json`
  - result: still flags 7 categories for future sub-classification.

## 覆蓋層級

- helper / formatter: covered。
- official generator: covered by generator report tests。
- DB replay artifact: covered。
- production DB write: not run by design。
- live Telegram: not run by design。

## 殘留風險

- Rule outcome audit still says hot / limit-up / quality-D categories need finer sub-classification.
- Current patch reduces hard-gate deadlock; it does not prove every candidate should become buyable.
