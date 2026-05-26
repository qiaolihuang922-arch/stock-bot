# v19.4 Strategy Diagnosis - 2026-05-26 Intraday

Scope: diagnostic only. No strategy, formatter, DB schema, or data-write logic was changed.

## 1. Data Correctness

05/26 intraday diagnostics produced valid data for all 12 watchlist stocks.

Key finding:
- `daily_source` was `yahoo` for all 12 stocks.
- `price_source` was `realtime` for all 12 stocks.
- TWSE daily K-line requests were not the active daily source in this run; Yahoo daily fallback supplied daily closes/volumes.
- Intraday `price` and `change` came from the same source: `realtime`.
- Current intraday strategy therefore mixes realtime price/change with daily K-line structure/volume from Yahoo fallback. This is acceptable as a design pattern, but the report should make this source split visible.
- Price-line parenthesis formatting is covered by the existing helper and should render as `價格：x（+y%）`.

| Stock | Price | Change | price_source | daily_source | Avg | PnL% | RR raw/display | Decision | Heat | Trade | Phase |
|---|---:|---:|---|---|---:|---:|---|---|---|---|---|
| 緯創 | 146.75 | -1.51% | realtime | yahoo | 136.80 | +7.27% | 2.70 / - | WAIT | NORMAL | NO_VOLUME | SHAKEOUT |
| 建準 | 163.25 | +0.46% | realtime | yahoo | - | - | 0.12 / - | WAIT | NORMAL | LATE_ENTRY | BREAKOUT_CONFIRM |
| 智原 | 210.25 | -3.78% | realtime | yahoo | 211.50 | -0.59% | 4.73 / - | BUY | NORMAL | NO_VOLUME | SHAKEOUT |
| 聯電 | 130.75 | +4.60% | realtime | yahoo | - | - | 0 / - | WAIT | EXTREME | AVOID | BREAKOUT_CONFIRM |
| 群創 | 46.225 | -5.86% | realtime | yahoo | - | - | 0 / - | WAIT | EXTREME | AVOID | BREAKOUT_CONFIRM |
| 華邦電 | 141.0 | +9.73% | realtime | yahoo | - | - | 0.23 / - | WAIT | EXTREME | AVOID | LOCK_LIMIT |
| 技嘉 | 336.25 | -0.07% | realtime | yahoo | 334.50 | +0.52% | 1.48 / - | WAIT | NORMAL | NO_VOLUME | SHAKEOUT |
| 南亞科 | 308.75 | +4.31% | realtime | yahoo | 298.00 | +3.61% | 4.67 / - | WAIT | NORMAL | NO_VOLUME | WEAK |
| 英業達 | 62.25 | -4.82% | realtime | yahoo | 52.15 | +19.37% | 0 / - | WAIT | HOT | EXTENDED | BREAKOUT_CONFIRM |
| 仁寶 | 33.325 | -3.82% | realtime | yahoo | - | - | 0.26 / 0.26 | WAIT | NORMAL | LATE_ENTRY | BREAKOUT_CONFIRM |
| 光寶科 | 237.25 | +4.29% | realtime | yahoo | - | - | 0.78 / 0.78 | WAIT | HOT | EXTENDED | BREAKOUT_CONFIRM |
| 旺宏 | 159.25 | +4.43% | realtime | yahoo | - | - | 2.44 / - | WAIT | NORMAL | NO_VOLUME | WEAK_REBOUND |

RR display finding:
- Holding stocks hide new-entry RR unless add is ready.
- EXTREME, weak, no-volume, far-from-trigger, weak-rebound states also hide RR.
- HOT but not EXTREME can still show RR, e.g. 光寶科 `0.78`.
- The rule is internally explainable, but the user-facing display feels inconsistent.

## 2. Why Most Unheld Stocks Are "Do Not Buy"

Unheld blockers across 7 stocks:

| Blocker | Count | Stocks |
|---|---:|---|
| RR不足 | 6 | 建準、聯電、群創、華邦電、仁寶、光寶科 |
| HOT/EXTREME | 4 | 聯電、群創、華邦電、光寶科 |
| 漲停不追 | 1 | 華邦電 |
| 量能不足 | 2 | 建準、聯電 |
| 市場弱 | 1 | 旺宏 |
| 遠離觸發 | 1 | 旺宏 |
| 弱反彈待確認 | 1 | 旺宏 |

Assessment:
- Correct strategic no-buy: 聯電、群創、華邦電、旺宏.
- Strategically valid wait, but display looks overly conservative: 建準、仁寶、光寶科.
- R3 market behavior is reasonable: many candidates are hot/extended and RR-blocked, so chasing should be forbidden.

Recommended v19.4 unheld grouping:
- 【禁止追高】: 華邦電、聯電、群創
- 【等待冷卻】: 光寶科
- 【弱勢淘汰】: 旺宏
- 【可觀察但不可買】: 建準、仁寶

Conclusion:
- The strategy is not simply too bearish.
- The display compresses several distinct states into `不買`, making the report feel more conservative than the strategy actually is.

## 3. Why Holdings Keep Showing Hold

Holding diagnostics:

| Stock | PnL% | price_behavior | heat | ext | phase | volume | VP | regime | trend | RR | level/action | reason | add_blockers |
|---|---:|---|---|---:|---|---|---|---|---|---:|---|---|---|
| 英業達 | +19.37% | VOLUME_DROP | HOT | 2 | BREAKOUT_CONFIRM | STRONG | NORMAL | RISK_ON | UP | 0 | HOLD / 續抱 | 突破成立，等量價確認再加碼 | 買點未成立、過熱不加碼、品質不足、RR不足、信心不足 |
| 緯創 | +7.27% | LOW_VOLUME_PULLBACK | NORMAL | 0 | SHAKEOUT | WEAK | COILING | NEUTRAL | UP | 2.7 | SHAKEOUT / 洗盤觀察 | 縮量回測，未見出貨 | 買點未成立、市場未轉強、量能不足 |
| 南亞科 | +3.61% | NORMAL | NORMAL | 1 | WEAK | WEAK | COILING | RISK_ON | UP | 4.67 | SHAKEOUT / 洗盤觀察 | 縮量回測，未見出貨 | 買點未成立、量能不足、品質不足、離突破太遠、信心不足 |
| 技嘉 | +0.52% | LOW_VOLUME_PULLBACK | NORMAL | 1 | SHAKEOUT | WEAK | COILING | RISK_ON | UP | 1.48 | SHAKEOUT / 洗盤觀察 | 縮量回測，未見出貨 | 浮盈不足、買點未成立、量能不足 |
| 智原 | -0.59% | LOW_VOLUME_PULLBACK | NORMAL | 1 | SHAKEOUT | WEAK | COILING | RISK_ON | UP | 4.73 | SHAKEOUT / 洗盤觀察 | 縮量回測，未見出貨 | 持倉未轉盈、量能不足 |

Key branch findings:
- `shakeout_protected` is too broad.
- The broadest branch is effectively: `volume=WEAK + volume_price_state=COILING + trend!=DOWN + pnl>-5`.
- This can protect stocks even when `structure_phase=WEAK` and distance is far from trigger, such as 南亞科.
- Warning branches are after shakeout protection, so light-loss + weak-volume holdings can become `洗盤觀察` instead of `警戒`.
- Profit-taking mostly needs `EXTREME` or `LIMIT_LOCK`.
- 英業達 has high profit, HOT, EXTENDED, and VOLUME_DROP, but does not trigger profit-taking or core-hold logic because it is not EXTREME and not LIMIT_LOCK.

## 4. Conclusions

Correct "do not buy":
- 聯電、群創、華邦電、旺宏.

Display-too-conservative "do not buy":
- 建準、仁寶、光寶科.

Reasonable holds:
- 緯創: washout hold is reasonable.
- 技嘉: hold is reasonable, but add language should remain blocked because profit is small and volume is weak.
- 智原: washout hold is acceptable, but because PnL is slightly negative it should carry warning wording.

Holds that should be upgraded:
- 英業達: should be `核心續抱` or `風控觀察`; current plain `續抱` is too weak for +19.37%, HOT, EXTENDED, VOLUME_DROP.
- 南亞科: should not be `洗盤觀察`; better as `續抱觀察` or `風控觀察` because phase is WEAK and trigger distance is far.
- 智原: keep washout logic but add warning tone due to slight loss.

## 5. v19.4 Recommendations

Strategy-condition changes:
1. Narrow `shakeout_protected`; at minimum exclude `phase=WEAK` with `breakout_distance > 4`.
2. Add high-profit pullback branch: `pnl>=15 + HOT/EXTENDED + VOLUME_DROP` should become `核心續抱` or `風控觀察`.
3. Move light-loss + weak-volume warning before broad shakeout protection, or split into `洗盤警戒`.
4. Split holding states more explicitly: `核心續抱`, `洗盤續抱`, `風控觀察`, `減碼`.

Display-only changes:
1. Split unheld report language into:
   - `禁止追高`
   - `等待冷卻`
   - `弱勢淘汰`
   - `可觀察但不可買`
2. Show `price_source` and `daily_source` clearly in intraday reports.
3. Normalize RR display wording so hidden RR explains why it is hidden.

Do not change yet:
- Do not change scoring before v19.4 strategy gates are finalized.
- Do not change DB/backfill logic for this diagnosis.
- Do not change Telegram layout until product confirms the taxonomy.
