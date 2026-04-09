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


# ===== 時段 =====
def get_phase():
    now = datetime.now(tz)
    if now.hour < 9:
        return "盤前"
    elif 9 <= now.hour <= 13:
        return "盤中🔥"
    else:
        return "盤後"


# ===== 主產出 =====
def generate():
    now = datetime.now(tz)
    phase = get_phase()

    msg = f"【{now.strftime('%m/%d')} {phase}｜AI交易系統】\n\n"

    for name, code in stocks.items():

        twse = get_twse(code)
        yahoo = get_yahoo(code)

        # ===== Debug =====
        print(f"{name} TWSE:", twse)
        print(f"{name} Yahoo:", yahoo)
        print("------")

        # ===== fallback =====
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
            use_realtime = False

            if now_time.hour > 9 or (now_time.hour == 9 and now_time.minute >= 2):
                use_realtime = True

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

        # ===== 分析 =====
        volume = volume_model(volumes, closes)
        trend = trend_model(price, ma5, ma20, closes, volumes)
        decision, buy, stop, position = strategy(price, ma5, ma20, closes, volumes)
        support, resistance = support_resistance(closes)

        # ===== 🔥 AI（關鍵修改）=====
        ai_text, is_real_ai = ai_analysis(
            name, price, change,
            ma5, ma20,
            volume, trend,
            decision, buy, stop
        )

        tag = "🧠AI" if is_real_ai else "⚠️Fallback"

        # ===== 組訊息 =====
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
        msg += f"{tag}：{ai_text}\n\n"

    return msg