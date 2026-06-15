# TASK: summary_brief_mobile_denoise_20260616

## Status

- task_id: `summary_brief_mobile_denoise_20260616`
- task_type: `normal_patch`
- status: `implemented`
- version: `v21.1`
- QA level: `L2`

## Owner Problem

Owner pasted the 06/16 pre-market decision brief and identified summary noise:

- `📎 詳情索引` has no value on mobile and should be removed.
- The decision brief contains fixed explanatory rows such as normal source line, generic reason, generic risk, and "持倉依第一則..." that do not change the decision.
- The summary should follow decision-dashboard practice: keep only actionable information and avoid clutter.

## User Visible Result

- Third Telegram message keeps:
  - market/action count line;
  - `新倉：無有效進場` or actual new-entry suggestion;
  - today pre-market/intraday risk-control plan;
  - holding control checklist;
  - unheld funnel/status;
  - rejected-count main reason when present.
- Third Telegram message removes:
  - `📎 詳情索引`;
  - normal `📡 資料：即時價 realtime｜日線 yahoo`;
  - generic `原因：...`;
  - generic `風險：...`;
  - `持倉：依第一則既有卡片處理，不新增第二個主行動。`;
  - `詳情見未持倉卡`.
- Abnormal source warnings remain allowed, for example stale `LAST_OHLCV` lines.

## Non Goals

- No strategy threshold change.
- No DB schema/write/backfill.
- No live Telegram delivery.
- No holding/unheld card strategy rewrite.
- No version bump; runtime remains `v21.1`.

## Impacted Modules And Direct Consumers

- `presentation/report.py`
- `core/generator.py`
- `tests/test_generator_report.py`
- Direct consumer: Telegram third summary/brief message.

## Output Contract

- Summary/brief is decision-first:
  - answer what to do today;
  - do not repeat where details are located;
  - do not show normal source plumbing;
  - keep abnormal data-source warning.
- `rejected_trace_line` should keep the rejected main reason but not tell the user to see details.
- `detail_index_text` may remain as an unused helper, but the official summary path must not render it.

## Version Contract

- Header remains `v21.1`.

## Acceptance Conditions

- Dry-run summary has zero `詳情索引`.
- Dry-run summary has zero normal `📡 資料`, zero `原因：`, zero `風險：`, zero `持倉：依第一則`, and zero `詳情見未持倉卡`.
- Dry-run summary still shows risk-control plan, holding control checklist, unheld status, and rejected main reason.
- Stale source warning regression remains covered.
- Full tests pass.
- No live Telegram delivery.

## Fixture / Failure Specimen

- Owner sample: 06/16 pre-market third message with `詳情索引`, generic data/reason/risk lines, and verbose summary clutter.
- Replay route:
  - local dry-run `generate_report(dry_run=True)`;
  - focused and full pytest.

## Forbidden And Blocking Conditions

- Do not hide actionable risk-control items.
- Do not hide abnormal source/stale data warnings.
- Do not change buy/sell/hold decisions.
