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
        d = r["quoteResponse"]["result"]

        if not d:
            return None, None, None

        d = d[0]

        return (
            d.get("regularMarketPrice"),
            d.get("regularMarketChangePercent"),
            d.get("regularMarketPreviousClose")
        )
    except:
        return None, None, None


# ========= Yahoo K線 =========
def get_history(code):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{code}.TW?range=1mo&interval=1d"
        r = requests.get(url, timeout=10).json()

        result = r["chart"]["result"][0]
        closes = result["indicators"]["quote"][0]["close"]
        volumes = result["indicators"]["quote"][0]["volume"]

        clean = []
        for i in range(len(closes)):
            if closes[i] and volumes[i]:
                clean.append((closes[i], volumes[i]))

        if len(clean) < 20:
            return None

        # ✅ 用最後完整K（避免抓到未完成）
        price = clean[-2][0]
        prev = clean[-3][0]

        ma5 = sum([x[0] for x in clean[-6:-1]]) / 5
        ma20 = sum([x[0] for x in clean[-21:-1]]) / 20

        vol = clean[-2][1]
        vol_avg = sum([x[1] for x in clean[-6:-1]]) / 5

        change = (price - prev) / prev * 100

        return price, prev, change, ma5, ma20, vol, vol_avg

    except:
        return None


# ========= TWSE fallback =========
def get_twse_price(code):
    try:
        url = f"https://www.twse.com.tw/exchangeReport/STOCK_DAY_AVG?response=json&stockNo={code}"
        r = requests.get(url, timeout=10).json()
        data = r.get("data")

        if not data:
            return None

        return float(data[-1][1])
    except:
        return None


# ========= 分析 =========
def analyze(price, prev, change, ma5, ma20, vol, vol_avg):

    if price is None:
        return "無資料", "觀望", None

    volume_strong = vol and vol_avg and vol > vol_avg * 1.5

    if ma5 and ma20:
        if price > ma5 > ma20:
            trend = "強勢多頭"
            buy = round(ma5, 1)
            suggestion = "回踩MA5買"

            if volume_strong:
                suggestion = "爆量回踩更佳"

        elif price > ma20:
            trend = "轉強"
            buy = round(ma20, 1)
            suggestion = "靠近MA20低接"

        else:
            trend = "弱勢"
            buy = None
            suggestion = "不進場"
    else:
        trend = "資料不足"
        buy = None
        suggestion = "觀望"

    return trend, suggestion, buy


# ========= 主流程 =========
def generate():

    today = datetime.now(tz).strftime("%m/%d")
    mode = "盤中模式" if is_market_open() else "收盤模式"

    msg = f"【{today} {mode} 多源交易系統】\n\n"

    best = None
    best_score = -999

    for name, code in stocks.items():

        # ===== 盤中 =====
        if is_market_open():

            price, change, prev = get_realtime(code)

            hist = get_history(code)

            if hist:
                _, _, _, ma5, ma20, vol, vol_avg = hist
            else:
                ma5 = ma20 = vol = vol_avg = None

        # ===== 收盤 =====
        else:
            hist = get_history(code)

            if hist:
                price, prev, change, ma5, ma20, vol, vol_avg = hist
            else:
                price = prev = change = ma5 = ma20 = vol = vol_avg = None

        # ===== fallback =====
        if price is None:
            price = get_twse_price(code)

        trend, suggestion, buy = analyze(price, prev, change, ma5, ma20, vol, vol_avg)

        if change and change > best_score:
            best_score = change
            best = name

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

    msg += f"👉 今日主攻：{best if best else '觀望'}"

    return msg


def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})


if __name__ == "__main__":
    send(generate())