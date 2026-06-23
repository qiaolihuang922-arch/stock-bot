# DISPATCH.md

## Active

- task_md_holds: `intraday_user_view_state_readability_v21_1_20260623`
- status: `implemented + focused verification passed + git completion passed`
- current_version: `v21.1`
- live Telegram delivery: `not run`
- DB schema change: `none`
- DB write/backfill/delete: `none`

## Result Summary

- Fixed 06/23 intraday user-visible contradictions in unheld cards.
- Overheated names now distinguish:
  - still strong / positive: keep `蝑?蒐.
  - pullback: `蝑?皜穿??葫蝣箄?`.
  - sharp pullback: `蝑?皜穿??交捏?葫`.
- Low-repair cards now show the actual missing level instead of repeating route text.
- Rejected cards suppress positive repair-history lines.

## User-Visible Contract

- Pullback overheat:
  - `????葫銝哨?閫撖?血?雿
  - `閫撖?撌脤?皞恬????寧??葫?臬摰?`
  - `??鞎琿?嚗?皜砌???+ ?蕭擃?+ ?銝仃?呎
- Sharp pullback:
  - `????交捏?葫嚗???
  - `??鞎琿?嚗?雿?皜祆??+ ?蕭擃?+ ?銝仃?呎
- Low repair:
  - `閫撖?餈??舀? X嚚??亙? Y嚚???Zx`
  - `?榆嚗?..`
  - `??鞎琿?嚗?餈??舀? X + 蝡?5?亙? Y + ?銝仃?呎

## Verification

- Focused new tests: `4 passed, 217 deselected`
- Related report subset: `25 passed, 196 deselected`
- Official dry-run: `messages=4`, no live Telegram.
- Full report test file note: `213 passed, 11 failed` due broader legacy expectations outside this focused task.

## Current Git State

- This cycle is committed and pushed to `origin/main`; git completion gate passed.

## Next Action

- Monitor the next 06/23-style intraday cards for title/body consistency.
- Separate follow-up: clean stale full-test expectations and summary/noise rules if Owner wants a full green report suite.
