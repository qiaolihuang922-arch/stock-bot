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


# ========= 判斷盤中 =========
def is_market_open():
    now = datetime.now(tz)
    return (9 <= now.hour < 13) or (now.hour == 13 and now.minute <= 30)


# ========= Yahoo =========
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

            for d in r["data"]:
                try:
                    rows.append({
                        "date": d[0],
                        "close": float(d[6].replace(",", "")),
                        "vol": float(d[1].replace(",", ""))
                    })
                except:
                    continue

        rows.sort(key=lambda x: x["date"])

        closes = [r["close"] for r in rows]
        volumes = [r["vol"] for r in rows]

        price = closes[-1]
        prev = closes[-2]
        change = (price - prev) / prev * 100

        ma5 = sum(closes[-5:]) / 5
        ma20 = sum(closes[-20:]) / 20

        return price, change, ma5, ma20, volumes, closes

    except:
        return None


# ========= 趨勢 =========
def analyze_trend(price, ma5, ma20, closes):

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


# ========= 量能 =========
def analyze_volume(volumes, change):

    vol = volumes[-1]
    avg10 = sum(volumes[-10:]) / 10
    ratio = vol / avg10

    if ratio > 2:
        level = "極爆量"
    elif ratio > 1.5:
        level = "爆量"
    elif ratio > 1.2:
        level = "放量"
    elif ratio < 0.8:
        level = "縮量"
    else:
        level = "正常"

    if change > 0 and ratio > 1.2:
        return f"{level}（趨勢確認）"
    elif change > 0 and ratio < 1:
        return f"{level}（假上漲）"
    elif change < 0 and ratio > 1.2:
        return f"{level}（出貨）"

    return level


# ========= 買點 =========
def get_buy_point(trend, ma5, ma20):

    if trend == "強勢多頭":
        return (round(ma5*0.99,1), round(ma5*1.01,1)), "回踩多頭支撐"

    elif trend == "多頭":
        return (round(ma20*0.99,1), round(ma20*1.01,1)), "回踩趨勢線"

    elif trend == "突破":
        return None, "等待回踩確認"

    else:
        return None, "不進場"


# ========= 主 =========
def generate():

    now = datetime.now(tz)
    mode = "盤中" if is_market_open() else "收盤"

    msg = f"【{now.strftime('%m/%d')} {mode}交易級系統】\n\n"

    for name, code in stocks.items():

        y = get_yahoo(code)
        t = get_twse(code)

        if not t:
            msg += f"📌 {name}\n→ 無資料\n\n"
            continue

        t_price, t_change, ma5, ma20, volumes, closes = t

        if is_market_open() and y:
            price, change = y
        else:
            price, change = t_price, t_change

        trend = analyze_trend(price, ma5, ma20, closes)
        volume = analyze_volume(volumes, change)
        buy, strategy = get_buy_point(trend, ma5, ma20)

        msg += f"📌 {name}\n"
        msg += f"→ 現價：{round(price,1)}\n"
        msg += f"→ 漲跌：{round(change,2)}%\n"
        msg += f"→ MA5：{round(ma5,1)}\n"
        msg += f"→ MA20：{round(ma20,1)}\n"
        msg += f"→ 量能：{volume}\n"
        msg += f"→ 趨勢：{trend}\n"

        if buy:
            msg += f"🔥 買點：{buy[0]} ~ {buy[1]}\n"
            msg += f"→ 策略：{strategy}\n"
        else:
            msg += f"⛔ {strategy}\n"

        msg += "\n"

    return msg


def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})


if __name__ == "__main__":
    send(generate())