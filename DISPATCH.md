# DISPATCH.md

## Active

- task_md_holds: `rr_context_standardization_v21_1_20260615`
- status: `implemented + production backfill verified`
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
- Owner applied `db/sql/v21_2_rr_context_columns.sql`; production read verified the new fields on `daily_signal_snapshot` and `signal_items`.
- Production `daily_signal_snapshot` RR component backfill completed through approved repo scripts.

## Verification

- Strategy/persistence/backfill/formatter/generator regression: `263 passed, 147 warnings, 44 subtests passed`.
- Official generator dry-run: `VERSION v21.1`, `messages 4`, no live Telegram delivery.
- Dry-run message list checked the Owner-style failure route, not only helper output.
- Production DB verification after backfill:
  - `daily_signal_snapshot`: 5786 rows, all `v21.1`.
  - RR component missing rows: 0.
  - exact duplicate `(stock_id, trade_date, version)` groups: 0.
  - old-version overlap rows: 0.
  - prune dry-run delete candidates: 0.
  - RR contexts: actionable 728, blocked 738, setup_pending 140, theoretical 4180.
- Warmup daily_price backfill wrote 664 rows for 2024-02-18 through 2024-06-16 so the earliest 2024-06-17 through 2024-06-28 snapshots could be recomputed without fake values.

## Current Git State

- branch: `main`
- upstream: `origin/main`
- HEAD/upstream checked at closeout; final response reports exact commit.
- worktree expected clean after git closeout.
- bash completion gate cannot run on this machine because WSL/Hyper-V is unavailable; Windows-equivalent git checks have been used.

## Next Action

- Next scheduled `run_mode=bot` should naturally write new `signal_items` rows with RR components; old historical `signal_items` runs were not reconstructed.
- Continue using approved repo scripts for any future backfill; do not hand-write production DML.
