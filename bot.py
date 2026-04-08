import requests
from datetime import datetime
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

# ========= Yahoo 即時 =========
def get_realtime(code):
    try:
        url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={code}.TW"
        r = requests.get(url, headers=HEADERS, timeout=10).json()

        data = r.get("quoteResponse", {}).get("result", [])
        if not data:
            return None, None

        d = data[0]
        return d.get("regularMarketPrice"), d.get("regularMarketChangePercent")

    except:
        return None, None


# ========= TWSE 多月K線 =========
def get_twse_history(code):
    try:
        closes = []
        volumes = []

        now = datetime.now(tz)

        # 抓3個月（確保>=20天）
        for i in range(3):
            month = (now.month - i - 1) % 12 + 1
            year = now.year if now.month - i > 0 else now.year - 1

            date_str = f"{year}{month:02d}"

            url = f"https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=json&date={date_str}&stockNo={code}"
            r = requests.get(url, headers=HEADERS, timeout=10).json()

            if r.get("stat") != "OK":
                continue

            data = r.get("data", [])

            for d in data:
                try:
                    closes.append(float(d[6].replace(",", "")))
                    volumes.append(float(d[1].replace(",", "")))
                except:
                    continue

        if len(closes) < 20:
            return None

        price = closes[-1]
        prev = closes[-2]
        change = (price - prev) / prev * 100

        ma5 = sum(closes[-5:]) / 5
        ma20 = sum(closes[-20:]) / 20

        vol = volumes[-1]
        vol_avg = sum(volumes[-5:]) / 5

        return price, change, ma5, ma20, vol, vol_avg

    except:
        return None


# ========= 買點區間 =========
def get_buy_zone(ma20):
    low = ma20 * 0.99
    high = ma20 * 1.01
    return round(low, 1), round(high, 1)


# ========= 分析 =========
def analyze(price, change, ma5, ma20, vol, vol_avg):

    volume_strong = vol and vol_avg and vol > vol_avg * 1.5

    if price > ma5 > ma20:
        trend = "強勢多頭"
        strategy = "回踩MA5附近進場"
        buy = get_buy_zone(ma5)

    elif price > ma20:
        trend = "轉強"
        strategy = "回踩MA20附近低接"
        buy = get_buy_zone(ma20)

    else:
        trend = "弱勢"
        strategy = "不進場"
        buy = None

    return trend, strategy, buy


# ========= 主流程 =========
def generate():

    today = datetime.now(tz).strftime("%m/%d")
    msg = f"【{today} 完整穩定版（無假數據）】\n\n"

    for name, code in stocks.items():

        # Yahoo
        y_price, y_change = get_realtime(code)

        # TWSE
        t_data = get_twse_history(code)

        if not t_data and not y_price:
            msg += f"📌 {name}\n→ 無法取得資料\n\n"
            continue

        if t_data:
            t_price, t_change, ma5, ma20, vol, vol_avg = t_data
        else:
            t_price = t_change = ma5 = ma20 = vol = vol_avg = None

        price = y_price if y_price else t_price
        change = y_change if y_change else t_change

        trend, strategy, buy = analyze(price, change, ma5, ma20, vol, vol_avg)

        msg += f"📌 {name}\n"
        msg += f"→ 現價：{round(price,1)}\n"
        msg += f"→ 漲跌：{round(change,2) if change else 0}%\n"

        msg += f"→ MA5：{round(ma5,1) if ma5 else '無'}\n"
        msg += f"→ MA20：{round(ma20,1) if ma20 else '無'}\n"

        if vol and vol_avg:
            msg += f"→ 量能：{'爆量' if vol > vol_avg*1.5 else '正常'}\n"

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