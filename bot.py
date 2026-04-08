import requests
from datetime import datetime

TOKEN = "8714533132:AAGEAYs-Q-oZJDwwBwwuB0MPb27mqnDtzxs"
CHAT_ID = "7119676798"

stocks = {
    "緯創": "3231",
    "建準": "2421",
    "智原": "3035"
}

# ========= 多數據源 =========

def get_yahoo_history(code):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{code}.TW?range=1mo&interval=1d"
        r = requests.get(url, timeout=10).json()

        result = r["chart"]["result"][0]
        closes = result["indicators"]["quote"][0]["close"]
        volumes = result["indicators"]["quote"][0]["volume"]

        closes = [c for c in closes if c]
        volumes = [v for v in volumes if v]

        if len(closes) < 20:
            return None

        price = closes[-1]
        prev = closes[-2]

        ma5 = sum(closes[-5:]) / 5
        ma20 = sum(closes[-20:]) / 20

        vol = volumes[-1]
        vol_avg = sum(volumes[-5:]) / 5

        change = (price - prev) / prev * 100

        return price, prev, change, ma5, ma20, vol, vol_avg

    except:
        return None


def get_twse_fallback(code):
    try:
        url = f"https://www.twse.com.tw/exchangeReport/STOCK_DAY_AVG?response=json&stockNo={code}"
        r = requests.get(url, timeout=10).json()
        data = r.get("data")

        if not data:
            return None

        return float(data[-1][1])  # 平均價
    except:
        return None


# ========= 分析核心 =========

def analyze(data, fallback_price):

    if data:
        price, prev, change, ma5, ma20, vol, vol_avg = data
    else:
        price = fallback_price
        prev = fallback_price
        change = None
        ma5 = ma20 = None
        vol = vol_avg = None

    # 無資料
    if price is None:
        return "無資料", "觀望", None

    # ===== 趨勢判斷 =====
    if ma5 and ma20:
        if price > ma5 > ma20:
            trend = "強勢多頭"
        elif price > ma20:
            trend = "轉強"
        else:
            trend = "弱勢"
    else:
        trend = "資料不足"

    # ===== 成交量判斷 =====
    volume_strong = False
    if vol and vol_avg:
        if vol > vol_avg * 1.5:
            volume_strong = True

    # ===== 買點邏輯（核心）=====
    buy_price = None
    suggestion = "觀望"

    if trend == "強勢多頭":
        if volume_strong:
            buy_price = round(ma5, 1)
            suggestion = "爆量回踩MA5買"
        else:
            buy_price = round(ma20, 1)
            suggestion = "回踩MA20買"

    elif trend == "轉強":
        if volume_strong:
            buy_price = round(ma20, 1)
            suggestion = "放量轉強可試單"
        else:
            suggestion = "觀察不追"

    elif trend == "弱勢":
        suggestion = "不進場"

    return trend, suggestion, buy_price, price, change, ma5, ma20, vol, vol_avg


# ========= 報告 =========

def generate_report():
    today = datetime.now().strftime("%m/%d")
    msg = f"【{today} 終極交易系統】\n\n"

    best = None
    best_score = -999

    for name, code in stocks.items():

        data = get_yahoo_history(code)
        fallback = get_twse_fallback(code)

        trend, suggestion, buy, price, change, ma5, ma20, vol, vol_avg = analyze(data, fallback)

        if change and change > best_score:
            best_score = change
            best = name

        msg += f"📌 {name}\n"
        msg += f"→ 現價：{round(price,1) if price else '無'}\n"
        msg += f"→ 漲跌：{round(change,2) if change else '無'}%\n"
        msg += f"→ MA5：{round(ma5,1) if ma5 else '無'}\n"
        msg += f"→ MA20：{round(ma20,1) if ma20 else '無'}\n"

        if vol and vol_avg:
            msg += f"→ 成交量：{'爆量' if vol > vol_avg*1.5 else '正常'}\n"

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
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": msg
    })


if __name__ == "__main__":
    send(generate_report())