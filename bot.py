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

# ========= Yahoo 即時 =========
def get_realtime(code):
    try:
        url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={code}.TW"
        r = requests.get(url, timeout=10).json()
        data = r.get("quoteResponse", {}).get("result", [])

        if not data:
            return None, None

        d = data[0]
        return d.get("regularMarketPrice"), d.get("regularMarketChangePercent")

    except:
        return None, None


# ========= TWSE =========
def get_twse(code):
    try:
        url = f"https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=json&stockNo={code}"
        r = requests.get(url, timeout=10).json()
        data = r.get("data")

        if not data:
            return None

        closes = []
        volumes = []

        for d in data:
            try:
                closes.append(float(d[6].replace(",", "")))
                volumes.append(float(d[1].replace(",", "")))
            except:
                continue

        if len(closes) < 5:
            return None

        price = closes[-1]
        prev = closes[-2]

        change = (price - prev) / prev * 100

        ma5 = sum(closes[-5:]) / 5 if len(closes) >= 5 else price
        ma20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else price

        vol = volumes[-1]
        vol_avg = sum(volumes[-5:]) / 5 if len(volumes) >= 5 else vol

        return price, change, ma5, ma20, vol, vol_avg

    except:
        return None


# ========= 分析 =========
def analyze(price, change, ma5, ma20, vol, vol_avg):

    if price is None:
        return "無資料", "觀望", None

    volume_strong = vol and vol_avg and vol > vol_avg * 1.5

    if price > ma5 > ma20:
        return "強勢多頭", "回踩MA5", round(ma5, 1)

    elif price > ma20:
        return "轉強", "靠MA20", round(ma20, 1)

    else:
        return "弱勢", "不進場", None


# ========= 主流程 =========
def generate():

    today = datetime.now(tz).strftime("%m/%d")
    msg = f"【{today} 穩定最終版】\n\n"

    for name, code in stocks.items():

        # 1️⃣ Yahoo
        price, change = get_realtime(code)

        # 2️⃣ TWSE
        twse = get_twse(code)

        if twse:
            t_price, t_change, ma5, ma20, vol, vol_avg = twse

            if price is None:
                price = t_price

            if change is None:
                change = t_change

        else:
            ma5 = ma20 = vol = vol_avg = None

        # 3️⃣ 🔥 強制保底（最關鍵）
        if price is None:
            price = 0

        if change is None:
            change = 0

        if ma5 is None:
            ma5 = price

        if ma20 is None:
            ma20 = price

        trend, suggestion, buy = analyze(price, change, ma5, ma20, vol, vol_avg)

        msg += f"📌 {name}\n"
        msg += f"→ 現價：{round(price,1)}\n"
        msg += f"→ 漲跌：{round(change,2)}%\n"
        msg += f"→ MA5：{round(ma5,1)}\n"
        msg += f"→ MA20：{round(ma20,1)}\n"
        msg += f"→ 趨勢：{trend}\n"

        if buy:
            msg += f"🔥 買點：{buy}\n"
            msg += f"→ 策略：{suggestion}\n"
        else:
            msg += f"⛔ {suggestion}\n"

        msg += "\n"

    return msg


def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})


if __name__ == "__main__":
    send(generate())