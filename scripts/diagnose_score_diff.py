"""只读诊断：定位两檔同条件标的综合分差异来源（如華邦2344 vs 群創3481）。
用法（能抓行情的环境）：
  PYTHONPATH=. python scripts/diagnose_score_diff.py 2344 3481
完全复用主流程取价/解包/评分；只读，不写库、不发 Telegram。"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import analysis
from core.generator import load_report_daily_kline, _report_daily_parts

FIELDS = [
    "decision", "decision_type", "action",
    "market_grade", "market_score", "market_regime",
    "structure_state", "structure_phase", "trend", "trend_bias",
    "volume_state", "volume_price_state",
    "rr", "risk", "entry_quality", "confidence_score", "strength",
    "heat_state", "extended_level", "breakout_state", "breakout_distance",
    "trade_state", "price_behavior", "lifecycle",
]


def run(code):
    daily, source, err = load_report_daily_kline(code)
    if not daily:
        print(f"\n[{code}] 取不到行情：{err}"); return None
    p = _report_daily_parts(daily)
    if not p:
        print(f"\n[{code}] kline 解析失败（{source}）"); return None
    result = analysis.strategy(p["price"], p["change"], p["ma5"], p["ma20"], p["closes"], p["volumes"])
    print(f"\n===== {code} | price={p['price']} change={p['change']} "
          f"ma5={round(p['ma5'],2)} ma20={round(p['ma20'],2)} src={source} =====")
    for f in FIELDS:
        if f in result:
            print(f"  {f:18}= {result[f]}")
    return result


def main(argv=None):
    codes = list(argv if argv is not None else sys.argv[1:]) or ["2344", "3481"]
    results = {c: run(c) for c in codes}

    valid = {c: r for c, r in results.items() if r}
    if len(valid) == 2:
        a, b = list(valid.keys())
        ra, rb = valid[a], valid[b]
        print(f"\n===== 差异对比 {a} vs {b} =====")
        for f in FIELDS:
            if ra.get(f) != rb.get(f):
                print(f"  {f:18}: {a}={ra.get(f)}  |  {b}={rb.get(f)}")
        print("\n判读：综合分基底 confidence_score 由 market/structure/trend/volume/rr/risk/"
              "breakout_distance/heat 扣分等加权；上面 != 的项即分差来源。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
