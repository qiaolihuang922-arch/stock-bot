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
    if 8 <= now.hour < 9:
        return "盤前"
    elif 9 <= now.hour < 12:
        return "盤中"
    elif 12 <= now.hour <= 13:
        return "收盤前"
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
                    rows.append((
                        d[0],
                        float(d[6].replace(",", "")),
                        float(d[1].replace(",", ""))
                    ))
                except:
                    continue

        if len(rows) < 20:
            return None

        # 排序
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

    if ratio > 2:
        base = "極爆量"
    elif ratio > 1.5:
        base = "爆量"
    elif ratio > 1.2:
        base = "放量"
    elif ratio < 0.8:
        base = "縮量"
    else:
        base = "正常"

    if change > 0 and ratio > 1.2:
        return f"{base}（趨勢確認）"
    elif change < 0 and ratio > 1.2:
        return f"{base}（出貨風險）"
    elif change > 0 and ratio < 1:
        return f"{base}（假上漲）"

    return base


# ========= 趨勢 =========
def trend_model(price, ma5, ma20, closes):

    ma5_prev = sum(closes[-6:-1]) / 5
    ma20_prev = sum(closes[-21:-1]) / 20

    slope_up = ma5 > ma5_prev and ma20 > ma20_prev
    momentum = price - closes[-2]

    high = max(closes[-5:])
    low = min(closes[-5:])

    if price > ma5 > ma20 and slope_up and momentum > 0:
        return "強勢多頭"
    elif price > ma20 and slope_up:
        return "多頭"
    elif price >= high:
        return "突破"
    elif price <= low:
        return "破位"
    else:
        return "震盪"


# ========= 策略 =========
def strategy(price, ma5, ma20, closes, volumes):

    ma20_prev = sum(closes[-21:-1]) / 20
    trend_up = price > ma20 and ma20 > ma20_prev

    breakout = price >= max(closes[-5:])
    momentum = price > closes[-2]

    vol = volumes[-1]
    avg10 = sum(volumes[-10:]) / 10
    vol_ok = vol > avg10 * 1.2

    score = sum([trend_up, breakout, momentum, vol_ok])

    if score == 4:
        decision = "進場"
    elif score == 3:
        decision = "觀察"
    else:
        decision = "不進場"

    buy = (round(ma5 * 0.99, 1), round(ma5 * 1.01, 1))

    return decision, buy


# ========= 主 =========
def generate():

    now = datetime.now(tz)
    phase = get_phase()

    msg = f"【{now.strftime('%m/%d')} {phase}｜最終系統】\n\n"

    for name, code in stocks.items():

        twse = get_twse(code)
        yahoo = get_yahoo(code)

        if not twse:
            msg += f"📌 {name}\n→ 無資料\n\n"
            continue

        t_price, t_change, ma5, ma20, closes, volumes = twse

        if phase == "盤中" and yahoo:
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

        if decision == "進場":
            msg += f"🔥 買點：{buy[0]} ~ {buy[1]}\n"
        else:
            msg += f"⛔ 建議觀望\n"

        msg += "\n"

    return msg


def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})


if __name__ == "__main__":
    send(generate())