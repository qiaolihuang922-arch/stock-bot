from datetime import datetime
import pytz

from services.learning import record_trade
from services.stock_api import get_twse, get_yahoo, get_realtime_price
from services.analysis import strategy
from core.condition_engine import condition_engine, summarize_conditions

tz = pytz.timezone("Asia/Taipei")

stocks = {
    "緯創": "3231",
    "建準": "2421",
    "智原": "3035"
}


# ================================
# 🔥 時間系統
# ================================
def get_market_phase():

    now = datetime.now(tz)
    h, m = now.hour, now.minute

    if now.weekday() >= 5:
        return "假日"

    if h == 8 and 30 <= m < 40:
        return "盤前"

    elif 9 <= h < 13:
        return "盤中"

    elif h == 13 and m >= 20:
        return "收盤"

    return "盤後"


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
# 🔥 基本翻譯（保留）
# ================================
def translate_conditions(cond_list):

    mapping = {
        "market": "大盤不對",
        "trend": "趨勢不對",
        "structure": "結構不夠強",
        "volume": "量能不夠",
        "event": "沒有進場訊號",
        "edge": "型態不漂亮",
        "risk": "風險太高",
        "rr": "報酬不夠"
    }

    return [mapping.get(c, c) for c in cond_list]


# ================================
# 🔥 NEW：Edge細節翻譯（核心升級）
# ================================
def explain_edge(result, decision_type):

    reasons = []

    # ===== breakout =====
    if decision_type == "breakout":

        if result.get("event_breakout") is False:
            reasons.append("尚未突破")

        if result.get("edge_consolidation") is False:
            reasons.append("盤整不夠")

        if result.get("edge_not_high_zone") is False:
            reasons.append("位置太高（不要追）")

        if result.get("edge_fake_breakout") is True:
            reasons.append("疑似假突破")

    # ===== pullback =====
    elif decision_type == "pullback":

        if result.get("event_pullback") is False:
            reasons.append("還沒回踩完成")

        if result.get("edge_first_pullback") is False:
            reasons.append("不是第一次回踩")

        if result.get("edge_ma20_trend") is False:
            reasons.append("MA20未走升")

        if result.get("edge_structure_hold") is False:
            reasons.append("結構沒守住")

    return reasons


# ================================
# 🔥 進場劇本
# ================================
def entry_plan(price, buy):

    if not buy:
        return "", "", 0

    diff = (price - buy) / buy

    if diff > 0.02:
        return "追高區（風險高）", "不要追，等回踩", diff
    elif diff > 0.005:
        return "偏高區", "可小倉或等回踩", diff
    elif diff >= -0.005:
        return "理想區", "可以進場", diff
    else:
        return "尚未觸發", "等待價格到位", diff


# ================================
# 🔥 評分
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
    phase = get_market_phase()

    msg = f"【{now.strftime('%m/%d')} {phase}】\n\n"

    decisions = []
    candidates = []

    for name, code in stocks.items():

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
                price, change = t_price, t_change
        else:
            price, change = yahoo
            closes = [price] * 20
            volumes = [1] * 20
            ma5 = price
            ma20 = price

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

        score = score_system(market, trend, structure, momentum, rr)
        score_text = score_to_text(score)

        decisions.append(decision)

        conditions = condition_engine(result)
        summary = summarize_conditions(conditions, decision)

        # ===== learning =====
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

        if decision == "BUY":
            candidates.append((decision_type, rr, risk, name, buy, stop, score))

        msg += f"【{name}】{score_text}\n"

        # ================= BUY =================
        if decision == "BUY":

            zone, action, diff = entry_plan(price, buy)

            msg += "👉 可以進場\n"

            if decision_type == "breakout":
                msg += "→ 突破（順勢）\n"
            else:
                msg += "→ 回踩（低風險）\n"

            msg += f"🎯 進場 {safe_round(buy)} ｜ 停損 {safe_round(stop)}\n"
            msg += f"📊 RR {rr} ｜ {risk_to_text(risk)}\n"

            msg += f"📍 位置：{zone}\n"
            msg += f"👉 操作：{action}\n"

            if diff > 0.02:
                msg += "❗ 已偏離進場點，避免追高\n"

        # ================= WAIT（升級） =================
        elif decision == "WAIT":

            msg += "👉 還不能做\n"

            # 🔥 先顯示 Edge（重點升級）
            edge_reasons = explain_edge(result, decision_type)

            if edge_reasons:
                for r in edge_reasons[:3]:
                    msg += f"- {r}\n"
            else:
                # fallback（舊機制）
                reasons = translate_conditions(summary)
                for r in reasons[:3]:
                    msg += f"- {r}\n"

            if "event" in summary:
                msg += "👉 等突破 / 訊號出現\n"

        # ================= NO TRADE =================
        else:

            msg += "👉 不要做\n"

            priority = ["market", "trend", "volume"]
            reasons = [r for r in summary if r in priority]

            reasons = translate_conditions(reasons)

            for r in reasons:
                msg += f"- {r}\n"

        msg += f"💰 現價 {safe_round(price)}（{safe_round(change,2)}%）\n\n"

    msg += "====================\n"

    if any(d == "BUY" for d in decisions):
        msg += "🟢 今天有機會，可以挑著做\n"
    else:
        msg += "⏳ 今天沒好機會，先觀望\n"

    if candidates:
        best = sorted(candidates, key=lambda x: (
            x[0] == "breakout",
            x[1],
            -x[2]
        ), reverse=True)[0]

        _, rr, risk, name, buy, stop, score = best

        msg += "\n🔥 今天最值得看的\n"
        msg += f"{name}\n"
        msg += f"👉 {safe_round(buy)} 附近優先觀察\n"

    return msg