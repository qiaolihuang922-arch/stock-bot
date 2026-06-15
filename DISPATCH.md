# DISPATCH.md

## Active

- task_md_holds: `rr_context_standardization_v21_1_20260615`
- status: `implemented`
- current_version: `v21.1`
- no live Telegram delivery in this cycle.

## Result Summary

- RR now follows the normal entry / stop / target contract and exposes the calculation inputs:
  - formula `(target-entry)/(entry-stop)`;
  - entry, stop, target, reward, risk, risk percent, target basis;
  - context: `actionable`, `setup_pending`, `theoretical`, `blocked`.
- Telegram report no longer says high RR is `達標` when setup is not actionable:
  - 緯創 / 仁寶 / 技嘉 show `理論RR ...（setup未成立）`;
  - 旺宏 shows `理論RR 2.21僅參考` while waiting for retest;
  - 聯電 RR不足 remains plain `RR 1.32｜需>=1.5`.
- Persistence path was extended through shared strategy feature fields for daily snapshots, signal items, and backfill.
- SQL artifact prepared, not executed: `db/sql/v21_2_rr_context_columns.sql`.

## Verification

- Strategy/persistence/backfill/formatter/generator regression: `263 passed, 147 warnings, 44 subtests passed`.
- Official generator dry-run: `VERSION v21.1`, `messages 4`, no live Telegram delivery.
- Dry-run message list checked the Owner-style failure route, not only helper output.

## Current Git State

- branch: `main`
- upstream: `origin/main`
- HEAD/upstream checked at closeout; final response reports exact commit.
- worktree expected clean after git closeout.
- bash completion gate cannot run on this machine because WSL/Hyper-V is unavailable; Windows-equivalent git checks have been used.

## Next Action

- Owner reviews/applies `db/sql/v21_2_rr_context_columns.sql` before typed RR fields exist in production DB.
- After migration, run existing backfill/write scripts; do not hand-write production DML.
