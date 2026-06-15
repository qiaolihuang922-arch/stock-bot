# TASK: unheld_card_mobile_denoise_20260616

## Status

- task_id: `unheld_card_mobile_denoise_20260616`
- task_type: `normal_patch`
- status: `implemented`
- version: `v21.1`
- QA level: `L2`

## Owner Problem

Owner pasted the 06/16 pre-market unheld report and pointed out repeated mobile-reading lines, then clarified that the fix must not dump every metric into every `等回測` card:

- `拆解` and `盤面` carry overlapping state information.
- `買點`, `不能買`, `還差`, and `可買條件` repeat the same decision in separate rows.
- The report should be smarter and strategy-granular, not a hard text rewrite.
- `距突破` must remain visible for every stock.

## User Visible Result

- Unheld cards no longer print standalone `拆解` / duplicate `盤面` state rows.
- Normal waiting/rejected unheld cards no longer repeat `交易狀態` when title + `進場` already convey the same decision.
- Non-actionable unheld cards now show a readable entry block:
  - `進場：...｜原因：...`
  - `缺口：...`
  - `可買：...`
- `距突破：...` remains a standalone line.
- Waiting/rejected cards scope details by state:
  - `等回測` shows retest/breakout-zone confirmation, not the full volume/quality/RR package.
  - `等冷卻` shows heat/cooling.
  - `等風險報酬` shows risk-reward gap.
  - `等型態` shows setup/quality gap.
  - `淘汰` shows the invalidation / repair requirement.
- Normal waiting/rejected cards suppress noisy `數據：...` rows; source/data failure cards still keep fail-closed evidence.
- `歷史：...` is shown only when it carries useful memory such as repair / positive weight / high-signal prior execution, not for ordinary repeated failure noise.
- Strategy fields are still computed separately; only presentation is denoised.
- Entry evidence is now selected before formatting, not generated as a full metric package and trimmed afterward.

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
  - existing `交易狀態` stays as the state-machine line;
  - `盤面` is kept only when it adds useful market detail;
  - `距突破：...` stays standalone;
  - `進場：...｜原因：...`;
  - `缺口：...`;
  - `可買：...`.
- Existing decision semantics must remain visible:
  - why not buy;
  - what is missing;
  - what unlocks a buy.
- Do not display every available metric for every blocker. Show the metric family relevant to the current `funnel_state`.
- The official generator path must consume structured entry evidence, not parse old `不能買` / `還差` text to decide what to hide.

## Version Contract

- Header remains `v21.1`.
- This task changes Telegram formatting, not strategy/DB version.

## Acceptance Conditions

- Dry-run unheld card does not show the wall-like `狀態` / `進場檢查` hard-concat format.
- Dry-run unheld card shows `進場` / `缺口` / `可買` as short decision lines.
- Dry-run keeps one `距突破` line per unheld card.
- Dry-run normal unheld waiting/rejected cards have no `數據：` metric dump.
- Dry-run normal unheld waiting/rejected cards do not repeat `交易狀態` when the same state is already in the title and `進場`.
- Dry-run suppresses ordinary `歷史` noise while keeping meaningful repair / execution memory available.
- Generator report tests pass.
- Regression test prevents standalone duplicate `拆解` / `買點` / `不能買` / `還差` rows from returning in the rebound-retest case.
- Regression test prevents `等回測` / `等型態` helper output from reintroducing volume/quality/RR metric packages outside their state scope.
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
