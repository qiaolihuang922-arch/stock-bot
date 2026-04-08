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

# ========= 判斷盤中 =========
def is_market_open():
    now = datetime.now(tz)
    if now.weekday() >= 5:
        return False
    return 9 <= now.hour < 13


# ========= Yahoo 即時 =========
def get_realtime(code):
    try:
        url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={code}.TW"
        r = requests.get(url, timeout=10).json()
        data = r["quoteResponse"]["result"]

        if not data:
            return None, None

        d = data[0]
        return d.get("regularMarketPrice"), d.get("regularMarketChangePercent")

    except:
        return None, None


# ========= TWSE K線（穩定核心） =========
def get_twse_kline(code):
    try:
        url = f"https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=json&stockNo={code}"
        r = requests.get(url, timeout=10).json()

        data = r.get("data")
        if not data or len(data) < 20:
            return None

        closes = []
        volumes = []

        for d in data:
            try:
                close = float(d[6].replace(",", ""))
                vol = float(d[1].replace(",", ""))
                closes.append(close)
                volumes.append(vol)
            except:
                continue

        if len(closes) < 20:
            return None

        # 🔥 MA（用最後完整日）
        ma5 = sum(closes[-5:]) / 5
        ma20 = sum(closes[-20:]) / 20

        price = closes[-1]
        prev = closes[-2]

        change = (price - prev) / prev * 100

        vol = volumes[-1]
        vol_avg = sum(volumes[-5:]) / 5

        return price, change, ma5, ma20, vol, vol_avg

    except:
        return None


# ========= 分析 =========
def analyze(price, change, ma5, ma20, vol, vol_avg):

    if price is None:
        return "無資料", "觀望", None

    volume_strong = vol and vol_avg and vol > vol_avg * 1.5

    if price > ma5 > ma20:
        trend = "強勢多頭"
        buy = round(ma5, 1)
        suggestion = "回踩MA5"

        if volume_strong:
            suggestion = "爆量更佳"

    elif price > ma20:
        trend = "轉強"
        buy = round(ma20, 1)
        suggestion = "靠MA20"

    else:
        trend = "弱勢"
        buy = None
        suggestion = "不進場"

    return trend, suggestion, buy


# ========= 主流程 =========
def generate():

    today = datetime.now(tz).strftime("%m/%d")
    mode = "盤中" if is_market_open() else "收盤"

    msg = f"【{today} {mode}模式（最終穩定版）】\n\n"

    for name, code in stocks.items():

        # 1️⃣ 先拿官方資料（最穩）
        data = get_twse_kline(code)

        if data:
            price, change, ma5, ma20, vol, vol_avg = data
        else:
            # fallback：即時
            price, change = get_realtime(code)
            ma5 = ma20 = vol = vol_avg = None

        trend, suggestion, buy = analyze(price, change, ma5, ma20, vol, vol_avg)

        msg += f"📌 {name}\n"
        msg += f"→ 現價：{round(price,1) if price else '無'}\n"
        msg += f"→ 漲跌：{round(change,2) if change else '無'}%\n"
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