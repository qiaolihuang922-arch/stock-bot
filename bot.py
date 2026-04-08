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


# ========= TWSE（嚴謹版） =========
def get_twse(code):
    try:
        rows = []

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
                    rows.append({
                        "date": d[0],
                        "close": float(d[6].replace(",", "")),
                        "vol": float(d[1].replace(",", ""))
                    })
                except:
                    continue

        if len(rows) < 10:
            return None

        # 🔥 排序（關鍵）
        rows.sort(key=lambda x: x["date"])

        closes = [r["close"] for r in rows]
        volumes = [r["vol"] for r in rows]

        price = closes[-1]
        prev = closes[-2]

        if price <= 0 or prev <= 0:
            return None

        change = (price - prev) / prev * 100

        # 🔥 嚴謹 MA
        ma5 = sum(closes[-5:]) / 5

        ma20 = None
        if len(closes) >= 20:
            ma20 = sum(closes[-20:]) / 20

        return price, change, ma5, ma20, volumes

    except:
        return None


# ========= 量能（專業版） =========
def analyze_volume(volumes, change):

    if len(volumes) < 10:
        return "資料不足"

    vol = volumes[-1]
    avg10 = sum(volumes[-10:]) / 10

    ratio = vol / avg10

    if ratio > 2:
        level = "極爆量"
    elif ratio > 1.5:
        level = "爆量"
    elif ratio > 1.1:
        level = "放量"
    elif ratio < 0.8:
        level = "縮量"
    else:
        level = "正常"

    # 🔥 量價關係
    if change > 0 and ratio > 1.2:
        return f"{level}（上漲放量✔）"
    elif change < 0 and ratio > 1.2:
        return f"{level}（下跌放量⚠）"
    elif change > 0 and ratio < 1:
        return f"{level}（無量上漲⚠）"

    return level


# ========= 買點 =========
def get_buy_zone(base):
    return round(base * 0.99, 1), round(base * 1.01, 1)


# ========= 分析 =========
def analyze(price, ma5, ma20):

    if ma5 is None:
        return "資料不足", "觀望", None

    if ma20 and price > ma5 > ma20:
        return "強勢多頭", "回踩MA5進場", get_buy_zone(ma5)

    elif ma20 and price > ma20:
        return "轉強", "回踩MA20進場", get_buy_zone(ma20)

    else:
        return "弱勢", "不進場", None


# ========= 主 =========
def generate():

    now = datetime.now(tz)
    mode = "盤中" if is_market_open() else "收盤"

    msg = f"【{now.strftime('%m/%d')} {mode}嚴謹版】\n\n"

    for name, code in stocks.items():

        yahoo = get_yahoo(code)
        twse = get_twse(code)

        if not yahoo and not twse:
            msg += f"📌 {name}\n→ 無法取得資料\n\n"
            continue

        if twse:
            t_price, t_change, ma5, ma20, volumes = twse
        else:
            continue

        # 🔥 價格選擇（不混用）
        if is_market_open() and yahoo:
            price, change = yahoo
        else:
            price, change = t_price, t_change

        volume_text = analyze_volume(volumes, change)
        trend, strategy, buy = analyze(price, ma5, ma20)

        msg += f"📌 {name}\n"
        msg += f"→ 現價：{round(price,1)}\n"
        msg += f"→ 漲跌：{round(change,2)}%\n"
        msg += f"→ MA5：{round(ma5,1)}\n"
        msg += f"→ MA20：{round(ma20,1) if ma20 else '無'}\n"
        msg += f"→ 量能：{volume_text}\n"
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