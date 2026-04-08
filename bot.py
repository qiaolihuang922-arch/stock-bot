import requests
from datetime import datetime, timedelta
import pytz

TOKEN = "8714533132:AAGEAYs-Q-oZJDwwBwwuB0MPb27mqnDtzxs"
CHAT_ID = "7119676798"

# 🔥 你提供的key

import os
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


stocks = {
    "緯創": "3231",
    "建準": "2421",
    "智原": "3035"
}

tz = pytz.timezone("Asia/Taipei")
HEADERS = {"User-Agent": "Mozilla/5.0"}


# ===== 🔥 AI分析（新增，不影響原系統）=====
def ai_analysis(name, price, change, ma5, ma20, volume, trend, decision, buy, stop):

    prompt = f"""
你是一位專業股票交易員，請分析：

股票：{name}
現價：{price}
漲跌：{change}%
MA5：{ma5}
MA20：{ma20}
量能：{volume}
趨勢：{trend}
決策：{decision}
買點：{buy}
停損：{stop}

請用人話給建議：
- 是否進場
- 風險
- 該怎麼做

限制：50字內，不要模板
"""

    try:
        url = "https://api.openai.com/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}]
        }

        res = requests.post(url, headers=headers, json=data, timeout=15).json()

        return res["choices"][0]["message"]["content"]

    except:
        return "AI分析失敗"


# ===== 以下全部保留你原本代碼 =====

def get_phase():
    now = datetime.now(tz)
    if now.hour < 9:
        return "盤前"
    elif 9 <= now.hour < 11:
        return "盤中🔥"
    elif 11 <= now.hour < 13:
        return "午盤"
    else:
        return "盤後"


def get_yahoo(code):
    try:
        url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={code}.TW"
        r = requests.get(url, headers=HEADERS, timeout=10).json()
        d = r["quoteResponse"]["result"]
        if not d:
            return None
        d = d[0]
        return d["regularMarketPrice"], d["regularMarketChangePercent"]
    except:
        return None


def get_twse(code):
    try:
        rows = []
        now = datetime.now(tz)

        for i in range(8):
            date = now - timedelta(days=30*i)
            url = f"https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=json&date={date.strftime('%Y%m01')}&stockNo={code}"
            r = requests.get(url, headers=HEADERS, timeout=10).json()

            if r.get("stat") != "OK":
                continue

            for d in r.get("data", []):
                try:
                    rows.append((
                        d[0],
                        float(d[6].replace(",", "")),
                        float(d[1].replace(",", ""))
                    ))
                except:
                    continue

        if len(rows) < 25:
            return None

        rows.sort(key=lambda x: x[0])

        closes = [x[1] for x in rows]
        volumes = [x[2] for x in rows]

        price = closes[-1]
        prev = closes[-2]

        change = (price - prev) / prev * 100

        ma5 = sum(closes[-5:]) / 5
        ma20 = sum(closes[-20:]) / 20

        return price, change, ma5, ma20, closes, volumes

    except:
        return None


def volume_model(volumes, closes):
    vol = volumes[-1]
    avg10 = sum(volumes[-10:]) / 10
    ratio = vol / avg10

    vol_trend = volumes[-1] > volumes[-2] > volumes[-3]
    accumulation = sum(volumes[-3:]) > avg10 * 3
    price_up = closes[-1] > closes[-2]

    if ratio > 2:
        level = "爆量"
    elif ratio > 1.5:
        level = "強放量"
    elif ratio > 1.2:
        level = "放量"
    elif ratio < 0.7:
        level = "縮量"
    else:
        level = "正常"

    if price_up and ratio > 1.3 and vol_trend and accumulation:
        return f"{level}（主升✔）"
    if ratio > 1.3 and not price_up:
        return f"{level}（出貨⚠）"
    if price_up and ratio < 1:
        return f"{level}（假突破⚠）"

    return level


def trend_model(price, ma5, ma20, closes, volumes):

    ma20_prev = sum(closes[-21:-1]) / 20
    slope = ma20 - ma20_prev

    recent_high = max(closes[-5:])
    prev_high = max(closes[-10:-5])
    recent_low = min(closes[-5:])
    prev_low = min(closes[-10:-5])

    higher_high = recent_high > prev_high
    higher_low = recent_low > prev_low

    resistance = max(closes[-10:])
    near_res = price >= resistance * 0.97

    if price > ma5 > ma20 and slope > 0 and higher_high and higher_low:
        if price > recent_high * 0.98:
            return "🔥主升段"
        return "👍多頭結構"

    if near_res:
        return "⚠高位震盪"

    if price > ma20 and slope > 0:
        return "多頭"

    if price < ma20 and slope < 0:
        return "空頭"

    return "震盪"


def support_resistance(closes):
    return round(min(closes[-10:]),1), round(max(closes[-10:]),1)


def strategy(price, ma5, ma20, closes, volumes):

    support, resistance = support_resistance(closes)

    vol = volumes[-1]
    avg10 = sum(volumes[-10:]) / 10

    volume_ok = vol > avg10 * 1.2
    momentum = price > closes[-2]
    trend_ok = price > ma20

    confirm = sum([volume_ok, momentum, trend_ok]) >= 2

    breakout = price > resistance

    recent_low = min(closes[-5:])
    prev_low = min(closes[-10:-5])
    structure_low = min(recent_low, prev_low)

    if price > resistance and vol > avg10 * 1.5:
        stop = max(resistance * 0.97, structure_low, ma5 * 0.98)
        stop = min(stop, price * 0.99)

        if (price - stop) / price > 0.08:
            return "不進場（風險過大）", "-", "-"

        return "進場🔥（強勢續漲）", "現價附近", round(stop,1)

    if breakout and confirm:
        stop = max(resistance * 0.97, structure_low, ma5 * 0.98)
        stop = min(stop, price * 0.99)

        if (price - stop) / price > 0.08:
            return "不進場（風險過大）", "-", "-"

        return "進場🔥（突破）", "現價附近", round(stop,1)

    if price >= ma5:
        if price > ma5 * 1.05:
            return "觀望（過高）", "-", "-"

        buy_price = min(ma5, support)

        stop = max(ma20 * 0.98, structure_low)
        stop = min(stop, buy_price * 0.97)

        if (buy_price - stop) / buy_price > 0.08:
            return "觀望（風險過大）", "-", "-"

        return "進場🔥（回檔）", f"{round(buy_price,1)}", round(stop,1)

    if price > ma20:
        stop = max(ma20 * 0.97, structure_low)
        stop = min(stop, price * 0.99)

        if (price - stop) / price > 0.08:
            return "觀望（風險過大）", "-", "-"

        return "進場🔥（轉強）", f"{round(ma20,1)}", round(stop,1)

    return "觀望", "-", "-"


def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})


def generate():
    now = datetime.now(tz)
    phase = get_phase()

    msg = f"【{now.strftime('%m/%d')} {phase}｜AI交易系統】\n\n"

    for name, code in stocks.items():

        twse = get_twse(code)
        yahoo = get_yahoo(code)

        if not twse:
            msg += f"{name}：無資料\n\n"
            continue

        t_price, t_change, ma5, ma20, closes, volumes = twse

        if "盤中" in phase and yahoo:
            price, change = yahoo
        else:
            price, change = t_price, t_change

        volume = volume_model(volumes, closes)
        trend = trend_model(price, ma5, ma20, closes, volumes)
        decision, buy, stop = strategy(price, ma5, ma20, closes, volumes)

        # 🔥 AI分析加入（不影響原系統）
        ai_text = ai_analysis(name, price, change, ma5, ma20, volume, trend, decision, buy, stop)

        support, resistance = support_resistance(closes)

        msg += f"{name}\n"
        msg += f"現價：{round(price,1)} | 漲跌：{round(change,2)}%\n"
        msg += f"MA5：{round(ma5,1)} | MA20：{round(ma20,1)}\n"
        msg += f"量能：{volume}\n"
        msg += f"趨勢：{trend}\n"
        msg += f"支撐：{support} 壓力：{resistance}\n"
        msg += f"決策：{decision}\n"
        msg += f"買點：{buy}\n"
        msg += f"停損：{stop}\n"
        msg += f"🤖 AI分析：{ai_text}\n\n"

    return msg


if __name__ == "__main__":
    send(generate())