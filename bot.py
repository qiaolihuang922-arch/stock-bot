import requests
from datetime import datetime, timedelta
import pytz

TOKEN = "8714533132:AAGEAYs-Q-oZJDwwBwwuB0MPb27mqnDtzxs"
CHAT_ID = "7119676798"

stocks = {
    "緯創": "3231",
    "建準": "2421",
    "智原": "3035"
}

tz = pytz.timezone("Asia/Taipei")
HEADERS = {"User-Agent": "Mozilla/5.0"}


# ========= 時段 =========
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


# ========= Yahoo =========
def get_yahoo(code):
    try:
        url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={code}.TW"
        r = requests.get(url, headers=HEADERS, timeout=10).json()
        d = r["quoteResponse"]["result"]
        if not d:
            return None
        d = d[0]
        price = d.get("regularMarketPrice")
        change = d.get("regularMarketChangePercent")
        if price and price > 0:
            return price, change
    except:
        return None


# ========= TWSE =========
def get_twse(code):
    try:
        rows = []
        now = datetime.now(tz)

        for i in range(4):
            date = now - timedelta(days=30*i)
            url = f"https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=json&date={date.strftime('%Y%m01')}&stockNo={code}"
            r = requests.get(url, headers=HEADERS, timeout=10).json()

            if r.get("stat") != "OK":
                continue

            for d in r["data"]:
                try:
                    rows.append((
                        d[0],
                        float(d[6].replace(",", "")),
                        float(d[1].replace(",", ""))
                    ))
                except:
                    continue

        if len(rows) < 20:
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


# ========= 量能（進化版） =========
def volume_model(volumes, closes):
    vol = volumes[-1]
    avg10 = sum(volumes[-10:]) / 10
    ratio = vol / avg10

    price_up = closes[-1] > closes[-2]

    # 累積量（最近3天）
    vol3 = sum(volumes[-3:])
    avg3 = avg10 * 3

    accumulation = vol3 > avg3

    if ratio > 1.5:
        level = "爆量"
    elif ratio > 1.2:
        level = "放量"
    elif ratio < 0.8:
        level = "縮量"
    else:
        level = "正常"

    if price_up and ratio > 1.2 and accumulation:
        return f"{level}（主力進場✔）"
    elif not price_up and ratio > 1.2:
        return f"{level}（出貨⚠）"
    elif price_up and ratio < 1:
        return f"{level}（假上漲⚠）"

    return level


# ========= 趨勢（進化版） =========
def trend_model(price, ma5, ma20, closes):

    ma5_prev = sum(closes[-6:-1]) / 5
    ma20_prev = sum(closes[-21:-1]) / 20

    slope_up = ma5 > ma5_prev and ma20 > ma20_prev

    higher_high = closes[-1] >= max(closes[-5:])
    higher_low = min(closes[-3:]) > min(closes[-6:-3])

    momentum = closes[-1] > closes[-2]

    if price > ma5 > ma20 and slope_up and higher_high and momentum:
        return "強勢多頭（確認）"
    elif price > ma20 and slope_up:
        return "多頭"
    elif price < ma20:
        return "空頭"
    else:
        return "震盪"


# ========= 策略（進化版） =========
def strategy(price, ma5, ma20, closes, volumes):

    ma20_prev = sum(closes[-21:-1]) / 20

    trend_ok = price > ma20 and ma20 > ma20_prev
    momentum = price > closes[-2]

    vol = volumes[-1]
    avg10 = sum(volumes[-10:]) / 10
    volume_ok = vol > avg10 * 1.2

    breakout = price >= max(closes[-5:])
    fake_breakout = breakout and not volume_ok

    # 🔥 一致性過濾（核心）
    if fake_breakout:
        return "不進場", "-", "-"

    score = sum([trend_ok, momentum, volume_ok, breakout])

    # 支撐壓力
    support = min(closes[-10:])
    resistance = max(closes[-10:])

    if score >= 3:
        decision = "進場🔥"

        # 不同情境買點
        if breakout:
            buy = f"突破回踩 {round(resistance,1)} 附近"
        else:
            buy = f"{round(ma5*0.99,1)} ~ {round(ma5*1.01,1)}"

    else:
        decision = "觀望"
        buy = "-"

    stop = round(ma20 * 0.98, 1)

    return decision, buy, stop


# ========= 主 =========
def generate():

    now = datetime.now(tz)
    phase = get_phase()

    msg = f"【{now.strftime('%m/%d')} {phase}｜進化最終版】\n\n"

    for name, code in stocks.items():

        twse = get_twse(code)
        yahoo = get_yahoo(code)

        if not twse:
            msg += f"📌 {name}\n→ 無資料\n\n"
            continue

        t_price, t_change, ma5, ma20, closes, volumes = twse

        if "盤中" in phase and yahoo:
            price, change = yahoo
        else:
            price, change = t_price, t_change

        volume = volume_model(volumes, closes)
        trend = trend_model(price, ma5, ma20, closes)
        decision, buy, stop = strategy(price, ma5, ma20, closes, volumes)

        msg += f"📌 {name}\n"
        msg += f"→ 現價：{round(price,1)}\n"
        msg += f"→ 漲跌：{round(change,2)}%\n"
        msg += f"→ MA5：{round(ma5,1)}\n"
        msg += f"→ MA20：{round(ma20,1)}\n"
        msg += f"→ 量能：{volume}\n"
        msg += f"→ 趨勢：{trend}\n"
        msg += f"👉 決策：{decision}\n"
        msg += f"🔥 買點：{buy}\n"
        msg += f"🛑 停損：{stop}\n\n"

    return msg


def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})


if __name__ == "__main__":
    send(generate())