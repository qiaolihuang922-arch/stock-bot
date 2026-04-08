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

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# ========= 判斷盤中 =========
def is_market_open():
    now = datetime.now(tz)
    return (9 <= now.hour < 13) or (now.hour == 13 and now.minute <= 30)


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

        if price is None or price <= 0:
            return None

        return price, change

    except:
        return None


# ========= TWSE =========
def get_twse(code):
    try:
        closes = []
        volumes = []
        dates = []

        now = datetime.now(tz)

        for i in range(4):
            date = now - timedelta(days=30 * i)
            date_str = date.strftime("%Y%m01")

            url = f"https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=json&date={date_str}&stockNo={code}"
            r = requests.get(url, headers=HEADERS, timeout=10).json()

            if r.get("stat") != "OK":
                continue

            for d in r.get("data", []):
                try:
                    dates.append(d[0])
                    closes.append(float(d[6].replace(",", "")))
                    volumes.append(float(d[1].replace(",", "")))
                except:
                    continue

        if len(closes) < 5:
            return None

        # 🔥 排序（避免亂序）
        combined = list(zip(dates, closes, volumes))
        combined.sort(key=lambda x: x[0])

        closes = [x[1] for x in combined]
        volumes = [x[2] for x in combined]

        price = closes[-1]
        prev = closes[-2]

        if price <= 0 or prev <= 0:
            return None

        change = (price - prev) / prev * 100

        ma5 = sum(closes[-5:]) / 5

        ma20 = None
        if len(closes) >= 20:
            ma20 = sum(closes[-20:]) / 20

        vol = volumes[-1]
        vol_avg = sum(volumes[-5:]) / 5

        return price, change, ma5, ma20, vol, vol_avg

    except:
        return None


# ========= 買點 =========
def get_buy_zone(ma):
    return round(ma * 0.99, 1), round(ma * 1.01, 1)


# ========= 分析 =========
def analyze(price, ma5, ma20, vol, vol_avg):

    if ma5 is None:
        return "資料不足", "觀望", None, False

    volume_strong = False
    if vol and vol_avg:
        volume_strong = vol > vol_avg * 1.5

    if ma20 and price > ma5 > ma20:
        return "強勢多頭", "回踩MA5進場", get_buy_zone(ma5), volume_strong

    elif ma20 and price > ma20:
        return "轉強", "回踩MA20進場", get_buy_zone(ma20), volume_strong

    else:
        return "弱勢", "不進場", None, volume_strong


# ========= 主 =========
def generate():

    now = datetime.now(tz)
    mode = "盤中" if is_market_open() else "收盤"

    msg = f"【{now.strftime('%m/%d')} {mode}優化穩定版】\n\n"

    for name, code in stocks.items():

        yahoo = get_yahoo(code)
        twse = get_twse(code)

        if not yahoo and not twse:
            msg += f"📌 {name}\n→ 無法取得資料\n\n"
            continue

        # 🔥 模式切換（不混用）
        if is_market_open() and yahoo:
            price, change = yahoo
        elif twse:
            price, change, ma5, ma20, vol, vol_avg = twse
        else:
            price, change = yahoo

        if twse:
            t_price, t_change, ma5, ma20, vol, vol_avg = twse
        else:
            ma5 = ma20 = vol = vol_avg = None

        trend, strategy, buy, vol_flag = analyze(price, ma5, ma20, vol, vol_avg)

        msg += f"📌 {name}\n"
        msg += f"→ 現價：{round(price,1)}\n"
        msg += f"→ 漲跌：{round(change,2) if change is not None else '無'}%\n"

        msg += f"→ MA5：{round(ma5,1) if ma5 else '無'}\n"
        msg += f"→ MA20：{round(ma20,1) if ma20 else '無'}\n"

        if vol and vol_avg:
            msg += f"→ 量能：{'爆量' if vol_flag else '正常'}\n"

        msg += f"→ 趨勢：{trend}\n"

        if buy:
            msg += f"🔥 買點區間：{buy[0]} ~ {buy[1]}\n"
            msg += f"→ 策略：{strategy}\n"
        else:
            msg += f"⛔ {strategy}\n"

        msg += "\n"

    return msg


def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": msg
    })


if __name__ == "__main__":
    send(generate())