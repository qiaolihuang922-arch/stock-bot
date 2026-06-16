# CHANGELOG: strategy_rule_outcome_audit_v21_1_20260616

## 修改內容與檔案

- `scripts/audit_strategy_rule_outcomes.py`
  - 新增 Supabase `daily_price` read-only outcome audit。
  - 對前一輪 replay event 補 1/3/5/10 日 forward return。
  - 計算每組平均報酬、勝率、平均 MFE、平均 MAE。
  - 依 `funnel_state / primary_blocker / decision_type / entry_quality / volume_state / heat_state` 分組。
  - 產生 `flags`，標出後續偏強但仍被 gate 擋住的規則。
- `tests/test_strategy_rule_outcomes.py`
  - 驗證 outcome 使用 forward DB 日線序列。
  - 驗證 read-only artifact contract。
  - 驗證偏強 blocker 會被標成 audit flag。
- `reports/audit/strategy_rule_outcomes_v21_1_20260616.json`
  - 產出本輪 rule outcome artifact。

## 契約影響

- 新增審計工具，不改正式策略。
- DB:
  - read-only select from `daily_price`。
  - 無 schema change。
  - 無 write/backfill/prune。
- Telegram:
  - 未改報文。
  - 未 live delivery。

## 版本同步

- Runtime 報文版本維持 `v21.1`。

## 直接消費者同步

- Owner / Architect 可用 artifact 判斷哪些 gate 需要下一輪策略修正。
- Production runner 不受影響。

## 未影響模組

- `core/generator.py` strategy/funnel 未改。
- `services/analysis.py` 策略計算未改。
- `presentation/report.py` 未改。

## 自檢命令與結果

- Targeted tests:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_strategy_rule_outcomes.py tests\test_strategy_buy_path_replay.py -q --tb=short`
  - result: `5 passed, 1 warning`
- Full:
  - `.\.venv\Scripts\python.exe -m pytest -q --tb=short`
  - result: `489 passed, 8 skipped, 165 warnings, 110 subtests passed`
- DB outcome replay:
  - `.\.venv\Scripts\python.exe scripts\audit_strategy_rule_outcomes.py --lookback-days 730 --version v21.1 --output reports\audit\strategy_rule_outcomes_v21_1_20260616.json`
  - result:
    - events: `5798`
    - events_with_10d_outcome: `5678`
    - flags: `7`

## 主要發現

- `可買` 組 5 日平均報酬 `+0.647%`，勝率 `48.43%`，屬 mixed，不是完全錯也不是強優勢。
- `等量能` 5 日平均報酬 `+0.221%`，勝率 `46.01%`，阻擋大致合理。
- `急彈待回測` 5 日平均報酬 `+0.1287%`，勝率 `42.86%`，等回測有依據。
- 需要下一輪策略檢討的 flags:
  - `隔日確認`: 5 日 `+8.5878%`，勝率 `78.26%`。
  - `漲停不追`: 5 日 `+3.288%`，勝率 `63.04%`。
  - `漲停反彈待確認`: 5 日 `+9.1624%`，勝率 `73.91%`。
  - `買點品質D`: 5 日 `+2.1268%`，勝率 `59.83%`。
  - `過熱觀察`: 5 日 `+6.1338%`，勝率 `61.67%`。
  - `wait_breakout_low_rr`: 5 日 `+3.7397%`，勝率 `57.46%`。
  - `HOT`: 5 日 `+5.5882%`，勝率 `61.76%`。

## 覆蓋層級

- production DB read-only: covered via `daily_price` replay。
- helper/script: covered。
- official generator: reused through previous replay event generation。
- runner artifact: not changed in this cycle。
- live Telegram: not run by design。

## 殘留風險

- Outcome replay 使用日收盤，不模擬盤中成交、滑價與停損觸發。
- flags 只代表「需要檢討」，不能直接等於「立刻買」。
- 下一輪若要修策略，應針對 flags 補分層規則，而不是硬改文案。
