# RESEARCH.md

## Topic: Breakout / Retest Strategy Evidence

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

## Local Buy-Path Replay

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

## Local Rule Outcome Replay

- Read-only DB outcome artifact:
  - `reports/audit/strategy_rule_outcomes_v21_1_20260616.json`
- Scope:
  - same 5798 stock-days
  - forward 1/3/5/10 day return, MFE and MAE
- Main flags:
  - `隔日確認`: 5 日 `+8.5878%`，勝率 `78.26%`
  - `漲停不追`: 5 日 `+3.288%`，勝率 `63.04%`
  - `漲停反彈待確認`: 5 日 `+9.1624%`，勝率 `73.91%`
  - `買點品質D`: 5 日 `+2.1268%`，勝率 `59.83%`
  - `過熱觀察`: 5 日 `+6.1338%`，勝率 `61.67%`
  - `wait_breakout_low_rr`: 5 日 `+3.7397%`，勝率 `57.46%`
  - `HOT`: 5 日 `+5.5882%`，勝率 `61.76%`

## Interpretation

- Current strategy can produce real buyable cases on historical DB data.
- `等回測` does not guarantee a later buy:
  - next-state replay shows it can become `可買`, `可準備`, `等冷卻`, `等RR修復`, `等接近`, or `淘汰`.
- Some conservative gates have statistical warning signs:
  - hot / limit-up related cases often continue after 5 days;
  - quality D is too broad and likely mixes weak structures with early repair structures;
  - low-RR breakout waiting may be too strict or may be using an overly conservative target/stop.

## Next Strategy Direction

- Do not turn all flags into buys.
- Split hot / limit-up cases:
  - no chase at lock price;
  - but allow next-day watch/prepare if support holds and volume remains valid.
- Split quality D:
  - weak D remains blocked;
  - repair D with multi-day rising close and support hold should become `等回測` or `可準備`, not permanent reject.
- Re-check RR:
  - validate target and stop anchors before using RR as a hard gate.
