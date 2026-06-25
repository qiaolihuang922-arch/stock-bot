# RESEARCH.md

## Topic

Breakout / retest / low-repair strategy evidence.

## Current Conclusion

- Breakout entries need a clear resistance/support level, volume confirmation, known risk/reward, and stop placement.
- Retest reduces false-breakout risk but is not automatically a buy.
- Low-repair and breakout are separate routes; a stock far from the old breakout zone can still be actionable through DB-backed low-repair conditions.
- Locked or overheated names are not chased; they wait for cooling or a tradable retest.

## v21.1 Contract

- Intraday complete low-repair can become `可買｜小倉` only when action-phase support, 5-day MA, non-chasing, volume, and RR conditions still hold.
- After-hours complete low-repair remains `可準備`.
- Strategy/backtest evidence affects confidence, ranking, or display context; market-data quality remains the hard gate.
- Source errors in auxiliary strategy evidence are not the same as unusable market data.

## Follow-Up

- Re-run DB replay for route-specific calibration: low-repair, breakout, hot/cooling, retest.
- Review whether quality grades need route-specific splits.
