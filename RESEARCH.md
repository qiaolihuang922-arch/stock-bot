# RESEARCH.md

## Topic: Breakout / Retest / Low-Repair Strategy Evidence

## Date

2026-06-22

## External Baseline

Common breakout and retest strategy references generally agree on these points:

- Breakout entries need a defined resistance / support level.
- Volume confirmation improves reliability.
- Pullback / retest confirmation reduces false-breakout risk.
- Do not chase extended or locked limit-up moves without a later tradable setup.
- Risk/reward and stop placement must be known before entry.

## Local Interpretation

- A retest is not automatically a buy. It is a candidate state that still needs confirmation.
- A stock far from the old breakout zone can still have a separate low-repair route if DB-backed conditions support it:
  - recent support holds
  - price stands above short moving average
  - volume is effective
  - risk/reward is acceptable
- Low-repair and breakout are different routes. The report must not force every candidate to wait for the old high if the current route is low-repair.

## Current v21.1 Contract

- `盤中` complete low-repair can become `可買｜小倉`.
- `盤後` / `收盤` complete low-repair remains `可準備`.
- Intraday low-repair is executable only if the action-phase report still satisfies support / 5-day MA / non-chasing / volume conditions.
- Low-repair should not depend on generic strategy sample availability once DB-backed low-repair conditions are available.
- Strategy / backtest evidence measures signal quality and economic value; it should affect confidence, ranking, or display context, not act as a standalone hard gate.
- Core market-data quality remains a hard gate: price, OHLCV, RR derivation, staleness, corruption, and conflict can fail closed.
- Strategy evidence source-error means "auxiliary evidence unavailable", not "market data unusable".
- Locked / overheated limit-up names are not chased; they wait for cooling or a tradable retest.

## Open Research Follow-Up

- Re-run DB replay for broader entry calibration:
  - low-repair route
  - breakout route
  - hot / cooling route
  - retest route
- Validate whether quality grades are too coarse and should be split into route-specific grades.
