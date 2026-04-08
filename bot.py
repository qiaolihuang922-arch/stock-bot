import requests
from datetime import datetime, timedelta
import pytz

# ✅ 不准刪
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
        data = r.get("quoteResponse", {}).get("result", [])
        if not data:
            return None

        d = data[0]
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
            date = now - timedelta(days=30 * i)
            url = f"https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=json&date={date.strftime('%Y%m01')}&stockNo={code}"
            r = requests.get(url, headers=HEADERS, timeout=10).json()

            if r.get("stat") != "OK":
                continue

            for d in r.get("data", []):
                try:
                    close = float(d[6].replace(",", ""))
                    vol = float(d[1].replace(",", ""))
                    rows.append((d[0], close, vol))
                except:
                    continue

        if len(rows) < 20:
            return None

        rows.sort(key=lambda x: x[0])

        closes = [x[1] for x in rows]
        volumes = [x[2] for x in rows]

        price = closes[-1]
        prev = closes[-2]

        if price <= 0 or prev <= 0:
            return None

        change = (price - prev) / prev * 100

        ma5 = sum(closes[-5:]) / 5
        ma20 = sum(closes[-20:]) / 20

        return price, change, ma5, ma20, closes, volumes

    except:
        return None


# ========= 量能 =========
def volume_model(volumes, change):
    if len(volumes) < 10:
        return "資料不足"

    vol = volumes[-1]
    avg10 = sum(volumes[-10:]) / 10
    ratio = vol / avg10

    if ratio > 1.5:
        base = "爆量"
    elif ratio > 1.2:
        base = "放量"
    elif ratio < 0.8:
        base = "縮量"
    else:
        base = "正常"

    if change > 0 and ratio > 1.2:
        return f"{base}（有效上漲）"
    elif change < 0 and ratio > 1.2:
        return f"{base}（出貨）"

    return base


# ========= 趨勢 =========
def trend_model(price, ma5, ma20, closes):
    ma5_prev = sum(closes[-6:-1]) / 5
    ma20_prev = sum(closes[-21:-1]) / 20

    slope = ma5 > ma5_prev and ma20 > ma20_prev
    momentum = price > closes[-2]

    if price > ma5 > ma20 and slope and momentum:
        return "強勢多頭"
    elif price > ma20 and slope:
        return "偏多"
    elif price < ma20:
        return "偏弱"
    else:
        return "震盪"


# ========= 策略 =========
def strategy(price, ma5, ma20, closes, volumes):

    ma20_prev = sum(closes[-21:-1]) / 20

    cond1 = price > ma20 and ma20 > ma20_prev
    cond2 = price > closes[-2]
    cond3 = volumes[-1] > sum(volumes[-10:]) / 10 * 1.2
    cond4 = price >= max(closes[-5:])

    score = sum([cond1, cond2, cond3, cond4])

    if score >= 3:
        decision = "進場🔥"
        buy_low = round(ma5 * 0.99, 1)
        buy_high = round(ma5 * 1.01, 1)
        buy = f"{buy_low} ~ {buy_high}"
    else:
        decision = "觀望"
        buy = "-"

    return decision, buy


# ========= 主 =========
def generate():
    now = datetime.now(tz)
    phase = get_phase()

    msg = f"【{now.strftime('%m/%d')} {phase}｜最終穩定版】\n\n"

    for name, code in stocks.items():

        twse = get_twse(code)
        yahoo = get_yahoo(code)

        if not twse:
            msg += f"📌 {name}\n→ 無法取得資料\n\n"
            continue

        t_price, t_change, ma5, ma20, closes, volumes = twse

        if "盤中" in phase and yahoo:
            price, change = yahoo
        else:
            price, change = t_price, t_change

        volume = volume_model(volumes, change)
        trend = trend_model(price, ma5, ma20, closes)
        decision, buy = strategy(price, ma5, ma20, closes, volumes)

        msg += f"📌 {name}\n"
        msg += f"→ 現價：{round(price,1)}\n"
        msg += f"→ 漲跌：{round(change,2)}%\n"
        msg += f"→ MA5：{round(ma5,1)}\n"
        msg += f"→ MA20：{round(ma20,1)}\n"
        msg += f"→ 量能：{volume}\n"
        msg += f"→ 趨勢：{trend}\n"
        msg += f"👉 決策：{decision}\n"
        msg += f"🔥 買點：{buy}\n\n"

    return msg


def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})


if __name__ == "__main__":
    send(generate())