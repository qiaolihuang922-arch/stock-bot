from datetime import datetime
import pytz

from services.learning import record_trade
from services.stock_api import get_twse, get_yahoo, get_realtime_price
from services.analysis import strategy

# ✅ 新增
from core.condition_engine import condition_engine, summarize_conditions

tz = pytz.timezone("Asia/Taipei")

stocks = {
    "緯創": "3231",
    "建準": "2421",
    "智原": "3035"
}


# ================================
# 🔥 工具
# ================================
def risk_to_text(risk):
    if risk >= 0.06:
        return "⚠️風險高"
    elif risk >= 0.03:
        return "⚠️風險中"
    return "✅風險低"


def score_to_text(score):
    if score >= 80:
        return "🔥 很強（可準備）"
    elif score >= 65:
        return "👍 不錯（差一步）"
    elif score >= 50:
        return "👌 普通（先觀察）"
    return "❌ 很弱（別碰）"


def safe_round(val, n=1):
    return round(val, n) if isinstance(val, (int, float)) else "-"


# ================================
# 🔥 評分（不影響 decision）
# ================================
def score_system(market, trend, structure, momentum, rr):

    score = 50

    if market == "STRONG":
        score += 10
    elif market == "WEAK":
        score -= 15

    if trend == "UP":
        score += 10
    elif trend == "DOWN":
        score -= 15

    if structure == "STRONG":
        score += 10
    elif structure == "WEAK":
        score -= 10

    if momentum == "ACCELERATING":
        score += 10
    elif momentum == "DECELERATING":
        score -= 5

    if rr >= 2:
        score += 10
    elif rr < 1.5:
        score -= 10

    return max(0, min(100, int(score)))


# ================================
# 🔥 主流程
# ================================
def generate():

    now = datetime.now(tz)
    msg = f"【{now.strftime('%m/%d')} 盤後】\n\n"

    decisions = []
    candidates = []

    for name, code in stocks.items():

        # ===== 取得資料 =====
        twse = get_twse(code)
        yahoo = get_yahoo(code)

        if not twse and not yahoo:
            continue

        if twse:
            t_price, t_change, ma5, ma20, closes, volumes = twse
            realtime = get_realtime_price(code)

            if realtime:
                price, change = realtime
            elif yahoo:
                price, change = yahoo
            else:
                price = t_price
                change = t_change
        else:
            price, change = yahoo
            closes = [price] * 20
            volumes = [1] * 20
            ma5 = price
            ma20 = price

        # ===== 策略 =====
        result = strategy(price, ma5, ma20, closes, volumes)

        decision = result.get("decision")
        decision_type = result.get("decision_type")
        buy = result.get("buy")
        stop = result.get("stop")
        risk = result.get("risk", 0)
        rr = result.get("rr", 0)

        market = result.get("market_signal")
        trend = result.get("trend")
        structure = result.get("structure_state")
        momentum = result.get("momentum_state")

        # ===== 評分 =====
        score = score_system(market, trend, structure, momentum, rr)
        score_text = score_to_text(score)

        decisions.append(decision)

        # ================================
        # 🔥 condition_engine（唯一條件來源）
        # ================================
        conditions = condition_engine(result)
        summary = summarize_conditions(conditions, decision)

        # ================================
        # 🔥 learning（不影響 decision）
        # ================================
        if decision == "BUY" and buy and stop and buy > stop:
            try:
                record_trade(
                    name, "buy", buy, buy, stop,
                    ma5, ma20, "-", "-",
                    extra_data={
                        "rr": rr,
                        "decision_type": decision_type,
                        "market": market,
                        "structure_state": structure,
                        "momentum_state": momentum
                    }
                )
            except:
                pass

        # ===== 候選 =====
        if decision == "BUY":
            candidates.append((decision_type, rr, risk, name, buy, stop, score))

        # ================================
        # 🔥 顯示層（完全遵守 v8）
        # ================================
        msg += f"【{name}】{score_text}\n"

        # ===== BUY =====
        if decision == "BUY":

            msg += "👉 進場條件成立\n"

            if decision_type == "breakout":
                msg += "→ 突破成立\n"
            elif decision_type == "pullback":
                msg += "→ 回踩成立\n"

            msg += f"🎯 {safe_round(buy)} / {safe_round(stop)}\n"
            msg += f"RR {rr} ｜ {risk_to_text(risk)}\n"

            if summary:
                msg += f"✅ 條件：{' / '.join(summary)}\n"

        # ===== WAIT =====
        elif decision == "WAIT":

            msg += "👉 尚未觸發\n"

            if summary:
                msg += f"缺少：{' / '.join(summary)}\n"

        # ===== NO TRADE =====
        else:

            msg += "👉 禁止交易\n"

            if summary:
                msg += f"原因：{' / '.join(summary)}\n"

        msg += f"💰 {safe_round(price)}（{safe_round(change,2)}%）\n\n"

    # ================================
    # 🔥 總結
    # ================================
    msg += "====================\n"

    if any(d == "BUY" for d in decisions):
        msg += "🟢 今天有機會，可以挑著做\n"
    else:
        msg += "⏳ 今天沒好機會，先觀望\n"

    # ================================
    # 🔥 最佳標的（符合 v8排序）
    # ================================
    if candidates:
        best = sorted(candidates, key=lambda x: (
            x[0] == "breakout",  # breakout優先
            x[1],                # RR
            -x[2]                # risk（越小越好）
        ), reverse=True)[0]

        _, rr, risk, name, buy, stop, score = best

        msg += "\n🔥 今天最值得看的\n"
        msg += f"{name}\n"
        msg += f"👉 {safe_round(buy)} 附近優先觀察\n"

    return msg