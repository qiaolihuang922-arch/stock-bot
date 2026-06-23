# QA_REPORT: intraday_display_state_sync_v21_1_20260623

## Test Scope

- Market phase handling around the 13:00 trading-day gap.
- Summary/card state consistency for overheat pullback names.
- Low-repair gap readability.
- Rejected-card primary reason clarity.
- Failed-breakout volume wording.
- Official dry-run message-list rendering.

## Risk Scan

- Strategy risk: medium. This changes visible state classification and wording, but does not change DB writes, schema, or live execution.
- DB risk: none.
- Live delivery risk: none.
- User misunderstanding risk reduced: summary now matches cards, failed breakout no longer sounds like positive attack volume, and low-repair cards say exactly how far from the needed MA.

## Cross-Block Semantic Consistency

- Overheat still rising: remains `等冷卻` / no chase.
- Overheat already pulling back: card and summary both treat it as `等回測`.
- Low repair: route, observation, missing condition, and effective buy point point to the same support / 5-day MA source.
- Rejected: title reason is concrete, not `觀察`.

## Failure Specimen Rebuttal

- Owner specimen: 06/23 report showed `非交易`, overheat-pullback summary mismatch, vague triggers, and unclear rejection labels.
- Dry-run rebuttal:
  - header: `【06/23 盤中｜v21.1】`.
  - summary: `未持倉 9｜僅追蹤 7（等冷卻3/等低位修復2/等回測2）｜淘汰 2`.
  - 旺宏: `盤面：突破失敗｜待確認｜放量回落`.
  - 緯創: `還差：站回5日均 161.2（差 2.45）`.
  - 仁寶: `還差：站回5日均 37.54（差 0.67）`.

## Commands And Results

- Focused tests: `7 passed, 217 deselected`.
- Related report subset: `26 passed, 198 deselected`.
- Official dry-run: `messages 4`, no live send.
- Full report file: `215 passed, 12 failed`; not accepted as full pass, residual test-contract debt remains.

## Not Tested

- Live Telegram delivery.
- Production DB write/read-after-write.
- DB backfill/prune/dedupe.

## QA Conclusion

conditional pass.

The 06/23 user-visible path is fixed by focused tests and official dry-run. Conditional because the full legacy report test file still has unrelated stale expectation failures that need a separate cleanup task.
