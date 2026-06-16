# RESEARCH.md

## Topic: Breakout / Retest Buy Path Sanity Check

## Date

2026-06-16

## External Baseline

- Breakout strategies commonly require:
  - resistance/support level identification;
  - price confirmation beyond the level;
  - volume confirmation;
  - pullback / retest confirmation to reduce false breakout risk;
  - predefined stop and positive risk/reward.
- A retest is not automatically a buy. It is a candidate state that still needs confirmation.
- Common failure modes:
  - false breakout;
  - pullback fails and falls back into the old range;
  - breakout is too extended / overbought;
  - volume does not confirm;
  - risk/reward no longer supports entry.

References reviewed:

- Investopedia: breakout trading requires strong levels, volume confirmation, planned exits and stop-loss.
- Investopedia: breakout on high volume has stronger continuation implication than low-volume breakout.
- StockCharts scanning guidance: consolidation + prior trend + breakout + sharp volume increase.
- Investopedia range-breakout risks: false breakouts and corrections back to breakout point are common.

## Local Replay Conclusion

- Read-only DB replay artifact:
  - `reports/audit/strategy_buy_path_replay_v21_1_20260616.json`
- Scope:
  - Supabase `daily_price`
  - 12 watchlist stocks
  - 2024-06-16 to 2026-06-16
  - 5798 stock-days
- Result:
  - `可買 / 趨勢延續`: 700 stock-days
  - `可買 / 趨勢延續 / 可準備`: 1035 stock-days
  - raw snapshot tradeable but blocked by funnel: 0 days
  - deadlock suspected: false

## Interpretation

- Current strategy can produce real buyable cases on historical DB data.
- `等回測` does not guarantee a later buy:
  - next-state replay shows it can become `可買`, `可準備`, `等冷卻`, `等RR修復`, `等接近`, or `淘汰`.
- This is consistent with common breakout/retest practice:
  - wait for retest;
  - buy only if retest holds and other gates remain valid.

## Follow-up Research

- If Owner wants execution-grade validation, next step is outcome replay:
  - when a signal was `可買`, compute next 1/3/5/10 day return, max drawdown and stop-hit rate.
- If Owner wants support-quality wording, implement real support sources:
  - swing low;
  - moving average support;
  - volume-by-price / price-volume shelf;
  - prior resistance turned support.
