# QA_REPORT: strategy_axis_split_v21_1_20260615

## Test Scope

- Strategy-axis split for unheld report cards.
- Derived analysis fields for strength/setup/actionability.
- Replay payload robustness when explicit behavior changes after raw result creation.
- Official generator mobile-reading output.

## Risk Scan

- If only text changes, the report may still flatten strength/setup/action into one D-like conclusion.
- If strength is treated as buyability, limit-up or overheated stocks may become chase recommendations.
- If stale derived payload fields are trusted over explicit behavior, replay artifacts can still show wrong strength labels.
- If actionability is too loose, waiting states can look like buy signals.

## Cross-Block Semantic Consistency

- Limit-up can be strong while action remains wait / no chase.
- Strong rebound can be improving while setup waits for retest.
- Risk/reward and setup quality remain blockers when not ready.
- Summary counts and card titles remain aligned with existing funnel states.
- No non-actionable card uses buy/recommendation wording.

## User Misread Risk

- Reduced: Owner can now read `強弱`, `買點`, and `行動` as separate ideas.
- Reduced: `D` no longer has to carry every meaning.
- Remaining by design: a stock can still be strong but not buyable if the setup is chase/cooldown/retest/RR-blocked.

## Failure Specimen Countercheck

- Official dry-run produced:
  - 華邦電: `強弱 強勢鎖價｜買點 等回測確認｜行動 等待`.
  - 旺宏: `強弱 急彈修復｜買點 等回測確認｜行動 等待`.
  - 聯電: `強弱 轉強中｜買點 等風險報酬｜行動 等待`.
- Targeted snapshots confirmed:
  - confirmed breakout: `STRONG` / `READY` / `BUYABLE`;
  - weak rebound: `WEAK_REBOUND` / `WAIT_RETEST`;
  - limit rebound: `REBOUND_STRONG` / `WAIT_RETEST`;
  - limit lock: `LIMIT_STRONG` / `CHASE_BLOCKED` / `NO_CHASE`.

## Evidence

- `258 passed, 149 warnings, 44 subtests passed`.
- Official dry-run generated the unheld message with split axes.
- No live Telegram delivery.
- No DB write or schema change.

## Not Tested

- Scheduled Render/GitHub runner after push.
- Live Telegram delivery.
- Production DB writes/backfills.

## QA Conclusion

通過

Reason: the tested paths prove this is not only a wording change. The analysis payload, official generator, and rendered card now carry separate strength/setup/action semantics.
