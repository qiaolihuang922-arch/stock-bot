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
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
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


# ========= TWSE K線 =========
def get_twse_data(code):
    try:
        now = datetime.now(tz)
        date_str = now.strftime("%Y%m")

        url = f"https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=json&date={date_str}&stockNo={code}"
        r = requests.get(url, headers=HEADERS, timeout=10).json()

        if r.get("stat") != "OK":
            return None

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

        if len(closes) < 2:
            return None

        price = closes[-1]
        prev = closes[-2]
        change = (price - prev) / prev * 100

        # 🔥 關鍵修正（永遠算）
        ma5 = sum(closes[-5:]) / min(5, len(closes))
        ma20 = sum(closes[-20:]) / min(20, len(closes))

        vol = volumes[-1] if volumes else None
        vol_avg = sum(volumes[-5:]) / min(5, len(volumes))

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
    msg = f"【{today} 完整穩定版】\n\n"

    for name, code in stocks.items():

        # 1️⃣ Yahoo（主）
        y_price, y_change = get_realtime(code)

        # 2️⃣ TWSE（補）
        t_data = get_twse_data(code)

        if t_data:
            t_price, t_change, ma5, ma20, vol, vol_avg = t_data
        else:
            t_price = t_change = ma5 = ma20 = vol = vol_avg = None

        # 3️⃣ 價格決策（優先Yahoo）
        price = y_price if y_price else t_price
        change = y_change if y_change else t_change

        # 4️⃣ 最後防呆（不給0假數據）
        if price is None:
            msg += f"📌 {name}\n→ 無法取得資料\n\n"
            continue

        trend, suggestion, buy = analyze(price, change, ma5, ma20, vol, vol_avg)

        msg += f"📌 {name}\n"
        msg += f"→ 現價：{round(price,1)}\n"
        msg += f"→ 漲跌：{round(change,2) if change else 0}%\n"
        msg += f"→ MA5：{round(ma5,1) if ma5 else '無'}\n"
        msg += f"→ MA20：{round(ma20,1) if ma20 else '無'}\n"

        if vol and vol_avg:
            msg += f"→ 量能：{'爆量' if vol > vol_avg*1.5 else '正常'}\n"

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
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": msg
    })


if __name__ == "__main__":
    send(generate())