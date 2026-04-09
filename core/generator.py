from datetime import datetime
import pytz

from services.stock_api import get_twse, get_yahoo, get_realtime_price
from services.analysis import volume_model, trend_model, strategy, support_resistance
from services.ai import ai_analysis

tz = pytz.timezone("Asia/Taipei")

stocks = {
    "緯創": "3231",
    "建準": "2421",
    "智原": "3035"
}


def get_phase():
    now = datetime.now(tz)
    if now.hour < 9:
        return "盤前"
    elif 9 <= now.hour <= 13:
        return "盤中🔥"
    else:
        return "盤後"


# ===== 時間權重 =====
def time_weight():
    now = datetime.now(tz)
    h, m = now.hour, now.minute

    if h < 9 or h > 13:
        return -3, "⛔ 非交易時段"

    if h == 9 and m < 30:
        return -2, "⚠ 開盤震盪"

    if (h == 9 and m >= 30) or h == 10:
        return 2, "🔥 主攻時段"

    if h >= 11:
        return -1, "⚠ 盤中震盪"

    return 0, ""


# ===== 🔥 全局決策（修正版）=====
def global_decision(decisions):
    score = 0
    strong_signal = False

    for d in decisions:
        if "進場🔥" in d:
            score += 3
            strong_signal = True
        elif "進場" in d:
            score += 2
        elif "試單" in d:
            score += 1
        elif "觀望" in d:
            score -= 1

    t_score, t_msg = time_weight()
    score += t_score

    # 🔥 必須有強訊號才允許買
    if score >= 2 and strong_signal:
        return f"🟢 能買（有機會） {t_msg}"
    else:
        return f"🔴 不能買（風險偏高） {t_msg}"


# ===== 評分 =====
def score_stock(decision, trend, volume, ai_text):
    score = 0

    if "進場🔥" in decision:
        score += 6
    elif "進場" in decision:
        score += 4
    elif "試單" in decision:
        score += 2

    if "主升" in trend:
        score += 3
    elif "轉強" in trend:
        score += 2

    if "主升" in volume:
        score += 3
    elif "強放量" in volume:
        score += 2
    elif "出貨" in volume:
        score -= 3

    if "高位" in trend:
        score -= 3

    if "BUY" in ai_text:
        score += 1
    elif "NO" in ai_text:
        score -= 2

    t_score, _ = time_weight()
    score += t_score

    return score


# ===== 行動建議（升級）=====
def build_action(decision, price, buy, position):
    if "進場🔥" in decision:
        return f"👉 現價進場（{position}）"

    elif "進場" in decision:
        return f"👉 回踩 {buy} 進場（{position}）"

    elif "試單" in decision:
        return f"👉 小倉試單（{position}）"

    elif buy != "-":
        return f"👉 等 {buy} 才進場"

    return ""


# ===== 預備買點（升級）=====
def get_prebuy(price, ma5, ma20, support, resistance, decision):

    if "觀望" not in decision:
        return "-"

    # 高位 → 等MA5
    if price > resistance * 0.97:
        return round(ma5, 1)

    # 跌破 → 等MA20或支撐
    if price < ma20:
        return round(max(ma20, support), 1)

    # 中間 → MA5 or support
    return round(max(ma5, support), 1)


# ===== 主產出 =====
def generate():
    now = datetime.now(tz)
    phase = get_phase()

    msg = f"【{now.strftime('%m/%d')} {phase}｜AI交易系統】\n\n"

    decisions = []
    candidates = []

    for name, code in stocks.items():

        twse = get_twse(code)
        yahoo = get_yahoo(code)

        if not twse:
            if not yahoo:
                msg += f"{name}：無資料\n\n"
                continue

            price, change = yahoo
            closes = [price] * 20
            volumes = [1] * 20
            ma5 = price
            ma20 = price

        else:
            t_price, t_change, ma5, ma20, closes, volumes = twse
            prev_close = closes[-2]

            now_time = datetime.now(tz)
            use_realtime = now_time.hour > 9 or (now_time.hour == 9 and now_time.minute >= 2)

            if use_realtime:
                realtime = get_realtime_price(code)

                if realtime:
                    price, change = realtime
                elif yahoo:
                    price, change = yahoo
                else:
                    price = t_price
                    change = (price - prev_close) / prev_close * 100
            else:
                price = t_price
                change = t_change

        volume = volume_model(volumes, closes)
        trend = trend_model(price, ma5, ma20, closes, volumes)
        decision, buy, stop, position = strategy(price, ma5, ma20, closes, volumes)
        support, resistance = support_resistance(closes)

        ai_text, is_real_ai = ai_analysis(
            name, price, change,
            ma5, ma20,
            volume, trend,
            decision, buy, stop
        )

        tag = "🧠AI" if is_real_ai else "⚠️Fallback"

        decisions.append(decision)

        pre_buy = get_prebuy(price, ma5, ma20, support, resistance, decision)

        s = score_stock(decision, trend, volume, ai_text)

        # 🔥 修正：允許試單進榜
        if buy != "-" and "觀望" not in decision:
            candidates.append((s, name, buy, stop))

        action = build_action(decision, price, buy, position)

        msg += f"{name}\n"
        msg += f"現價：{round(price,1)} | 漲跌：{round(change,2)}%\n"
        msg += f"MA5：{round(ma5,1)} | MA20：{round(ma20,1)}\n"
        msg += f"量能：{volume}\n"
        msg += f"趨勢：{trend}\n"
        msg += f"支撐：{support} 壓力：{resistance}\n"
        msg += f"決策：{decision}\n"
        msg += f"買點：{buy}\n"
        msg += f"停損：{stop}\n"
        msg += f"倉位：{position}\n"
        msg += f"預備買點：{pre_buy}\n"
        msg += f"{tag}：{ai_text}\n"
        msg += f"{action}\n\n"

    final = global_decision(decisions)
    _, t_msg = time_weight()

    msg += "====================\n"
    msg += f"{final}\n"

    if t_msg:
        msg += f"{t_msg}\n"

    if candidates:
        best = sorted(candidates, reverse=True)[0]
        score, name, buy, stop = best

        msg += "\n🔥 今日最佳標的\n"
        msg += f"{name}（分數:{score}）\n"
        msg += f"👉 買點：{buy}\n"
        msg += f"👉 停損：{stop}\n"

    return msg