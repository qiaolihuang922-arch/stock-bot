from datetime import datetime
import pytz

from services.stock_api import get_twse, get_yahoo, get_realtime_price
from services.analysis import *
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


def generate():
    now = datetime.now(tz)
    phase = get_phase()

    msg = f"【{now.strftime('%m/%d')} {phase}｜AI交易系統】\n\n"

    for name, code in stocks.items():

        twse = get_twse(code)
        yahoo = get_yahoo(code)

        if not twse:
            if not yahoo:
                msg += f"{name}：無資料\n\n"
                continue

            price, change = yahoo
            msg += f"{name}\n現價：{price} | 漲跌：{change}%\n⚠ Yahoo備援\n\n"
            continue

        t_price, t_change, ma5, ma20, closes, volumes = twse

        price = t_price
        change = t_change

        volume = volume_model(volumes, closes)
        trend = trend_model(price, ma5, ma20, closes, volumes)
        decision, buy, stop, position = strategy(price, ma5, ma20, closes, volumes)
        support, resistance = support_resistance(closes)

        ai_text = ai_analysis(name, price, change, ma5, ma20, volume, trend, decision, buy, stop, resistance)

        msg += f"{name}\n現價：{price} | 漲跌：{change}%\n"
        msg += f"決策：{decision}\n\n"

    return msg