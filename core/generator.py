from datetime import datetime
import pytz

from services.learning import record_trade
from services.stock_api import get_twse, get_yahoo, get_realtime_price
from services.analysis import strategy
from services.ai import ai_analysis

tz = pytz.timezone("Asia/Taipei")

stocks = {
    "緯創": "3231",
    "建準": "2421",
    "智原": "3035"
}


# ===== 風險轉文字 =====
def risk_to_text(risk):
    if risk >= 0.06:
        return "⚠️高風險"
    elif risk >= 0.03:
        return "⚠️中風險"
    return "✅低風險"


# ===== 市場總結 =====
def global_decision(decisions):
    buy = sum(1 for d in decisions if d == "BUY")
    no = sum(1 for d in decisions if d == "NO_TRADE")

    if buy >= 1:
        return "🟢 市場有機會（可操作）"
    if no == len(decisions):
        return "🔴 全面弱勢（不操作）"
    return "⏳ 觀望市場"


# ===== 主流程 =====
def generate():

    now = datetime.now(tz)
    msg = f"【{now.strftime('%m/%d')} 盤後｜AI交易系統】\n\n"

    decisions = []
    candidates = []

    for name, code in stocks.items():

        twse = get_twse(code)
        yahoo = get_yahoo(code)

        if not twse and not yahoo:
            msg += f"{name}：無資料\n\n"
            continue

        # ===== 價格處理 =====
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

        # ===== 🔥 核心決策 =====
        result = strategy(price, ma5, ma20, closes, volumes)

        decision = result["decision"]
        decision_type = result["decision_type"]
        buy = result["buy"]
        stop = result["stop"]
        risk = result["risk"]
        rr = result["rr"]

        risk_text = risk_to_text(risk)

        # ===== AI解釋（正確位置🔥）=====
        ai = ai_analysis(
            name=name,
            decision=decision,
            decision_type=decision_type,
            price=price,
            change=change,
            risk=risk,
            rr=rr
        )
        reason = ai.get("reason", "")

        decisions.append(decision)

        # ===== 記錄（fail-safe）=====
        if decision == "BUY" and buy and stop and buy > stop:
            try:
                record_trade(
                    name, "buy", buy, buy, stop,
                    ma5, ma20, "-", "-",
                    extra_data={
                        "rr": rr,
                        "decision_type": decision_type
                    }
                )
            except:
                pass

        # ===== 選最佳（v6排序）=====
        if decision == "BUY":
            candidates.append((decision_type, rr, risk, name, buy, stop))

        # ===== 顯示（優化版🔥）=====
        if decision == "BUY":

            entry_type = "突破" if decision_type == "breakout" else "回踩"

            msg += f"【{name}】🟢 可進場（{entry_type}）\n"
            if reason:
                msg += f"👉 {reason}\n"

            msg += f"🎯 進場：{round(buy,1)} ｜ 停損：{round(stop,1)}\n"
            msg += f"📊 RR：{rr} ｜ {risk_text}\n"
            msg += f"💰 現價：{round(price,1)}（{round(change,2)}%）\n\n"

        elif decision == "WAIT":

            msg += f"【{name}】⏳ 觀望\n"
            if reason:
                msg += f"👉 {reason}\n"

            msg += f"💰 現價：{round(price,1)}（{round(change,2)}%）\n\n"

        else:

            msg += f"【{name}】🚫 不做\n"
            if reason:
                msg += f"👉 {reason}\n"

            msg += f"💰 現價：{round(price,1)}（{round(change,2)}%）\n\n"

    msg += "====================\n"
    msg += f"{global_decision(decisions)}\n"

    # ===== 最佳標的 =====
    if candidates:
        best = sorted(candidates, key=lambda x: (
            x[0] == "breakout",
            x[1],
            -x[2]
        ), reverse=True)[0]

        _, rr, name, buy, stop = best

        msg += "\n🔥 今日最佳標的\n"
        msg += f"{name}\n"
        msg += f"🎯 {round(buy,1)} / {round(stop,1)}（RR:{rr}）\n"

    return msg