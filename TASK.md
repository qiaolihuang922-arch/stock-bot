# TASK: unheld_card_mobile_denoise_20260616

## Status

- task_id: `unheld_card_mobile_denoise_20260616`
- task_type: `normal_patch`
- status: `implemented`
- version: `v21.1`
- QA level: `L2`

## Owner Problem

Owner pasted the 06/16 pre-market unheld report and pointed out repeated mobile-reading lines:

- `拆解` and `盤面` carry overlapping state information.
- `買點`, `不能買`, `還差`, and `可買條件` repeat the same decision in separate rows.
- The report should be smarter and strategy-granular, not a hard text rewrite.

## User Visible Result

- Unheld cards now merge strategy state and market state into one `狀態` line.
- Unheld cards now merge entry decision, blocker, gap, and unlock into one `進場檢查` line.
- Strategy fields are still computed separately; only presentation is compacted.

## Non Goals

- No strategy threshold change.
- No DB schema/write/backfill.
- No live Telegram delivery.
- No holding-card rewrite.
- No version bump; runtime remains `v21.1` because this is presentation denoise inside the same strategy contract.

## Impacted Modules And Direct Consumers

- `presentation/report.py`
- `tests/test_generator_report.py`
- Direct consumer: Telegram unheld card message.

## Output Contract

- Non-actionable unheld cards should not print standalone duplicate lines:
  - `拆解：...`
  - `買點：...`
  - `不能買：...`
  - `還差：...`
- Replacement lines:
  - `狀態：強弱 ...｜買點 ...｜行動 ...｜盤面：...` when market detail is available.
  - `進場檢查：買點：...｜不能買：...｜還差：...｜可買條件：...`
- Existing decision semantics must remain visible:
  - why not buy;
  - what is missing;
  - what unlocks a buy.

## Version Contract

- Header remains `v21.1`.
- This task changes Telegram formatting, not strategy/DB version.

## Acceptance Conditions

- Dry-run unheld card shows merged `狀態` / `進場檢查`.
- Generator report tests pass.
- Regression test prevents standalone duplicate `拆解` / `買點` / `不能買` / `還差` rows from returning in the rebound-retest case.
- No live Telegram delivery.

## Fixture / Failure Specimen

- Owner sample: 06/16 pre-market unheld report showing separate `拆解`, `盤面`, `買點`, `不能買`, `還差`, `可買條件`.
- Replay route:
  - local dry-run `generate_report(dry_run=True)`;
  - focused generator tests.

## Forbidden And Blocking Conditions

- Do not remove decision detail by blindly deduplicating.
- Do not make weak/overheated/retest/RR blockers look buyable.
- Do not alter strategy decisions to satisfy presentation.
