import requests
from datetime import datetime, timedelta
import pytz

TOKEN = "8714533132:AAGEAYs-Q-oZJDwwuB0MPb27mqnDtzxs"
CHAT_ID = "7119676798"

stocks = {
    "緯創": "3231",
    "建準": "2421",
    "智原": "3035"
}

tz = pytz.timezone("Asia/Taipei")
HEADERS = {"User-Agent": "Mozilla/5.0"}


def get_phase():
    now = datetime.now(tz)
    if now.hour < 9:
        return "盤前"
    elif 9 <= now.hour < 11:
        return "盤中🔥"
    elif 11 <= now.hour < 13:
        return "午盤"
    else:
        return "盤後"


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


def get_twse(code):
    try:
        rows = []
        now = datetime.now(tz)

        for i in range(4):
            date = now - timedelta(days=30*i)
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

        rows.sort(key=lambda x: x[0])

        closes = [x[1] for x in rows]
        volumes = [x[2] for x in rows]

        price = closes[-1]
        prev = closes[-2]

        change = (price - prev) / prev * 100

        ma5 = sum(closes[-5:]) / 5
        ma20 = sum(closes[-20:]) / 20

        return price, change, ma5, ma20, closes, volumes

    except:
        return None


# ========= 強化量能 =========
def volume_model(volumes, closes):
    vol = volumes[-1]
    avg10 = sum(volumes[-10:]) / 10
    ratio = vol / avg10

    vol_trend = volumes[-1] > volumes[-2] > volumes[-3]
    accumulation = sum(volumes[-3:]) > avg10 * 3
    price_up = closes[-1] > closes[-2]

    if ratio > 1.5:
        level = "爆量"
    elif ratio > 1.2:
        level = "放量"
    elif ratio < 0.8:
        level = "縮量"
    else:
        level = "正常"

    if price_up and ratio > 1.2 and vol_trend and accumulation:
        return f"{level}（主升動能✔）"
    elif ratio > 1.2 and not price_up:
        return f"{level}（出貨⚠）"
    elif price_up and ratio < 1:
        return f"{level}（假漲⚠）"

    return level


# ========= 🔥終極趨勢 =========
def trend_model(price, ma5, ma20, closes):

    ma5_prev = sum(closes[-6:-1]) / 5
    ma20_prev = sum(closes[-21:-1]) / 20

    ma5_slope = ma5 - ma5_prev
    ma20_slope = ma20 - ma20_prev

    recent_high = max(closes[-5:])
    prev_high = max(closes[-10:-5])

    recent_low = min(closes[-5:])
    prev_low = min(closes[-10:-5])

    higher_high = recent_high > prev_high
    higher_low = recent_low > prev_low

    momentum = sum([closes[i] > closes[i-1] for i in range(-5,0)]) >= 3

    pullback = (recent_high - price) / recent_high

    # 🔥 分層開始

    if price > ma5 > ma20 and ma20_slope > 0:

        if higher_high and higher_low and momentum:

            if pullback < 0.03:
                return "🔥主升段（強）"
            elif pullback < 0.07:
                return "🚀加速段"
            else:
                return "👍多頭回檔"

        return "👍多頭"

    if price > ma20:
        return "⚠️高位震盪"

    if price < ma5 and ma5_slope < 0:
        return "❌轉弱"

    return "🧊空頭"


# ========= 策略 =========
def strategy(price, ma5, ma20, closes, volumes):

    ma20_prev = sum(closes[-21:-1]) / 20

    trend_ok = price > ma20 and ma20 > ma20_prev
    momentum = price > closes[-2]

    vol = volumes[-1]
    avg10 = sum(volumes[-10:]) / 10
    volume_ok = vol > avg10 * 1.2

    resistance = max(closes[-10:])
    support = min(closes[-10:])

    breakout = price > resistance

    if price >= resistance and not volume_ok:
        return "不進場", "-", "-", support, resistance

    score = sum([trend_ok, momentum, volume_ok, breakout])

    if score >= 3:
        decision = "進場🔥"
    else:
        decision = "觀望"

    # ========= 買點（修正錯誤） =========
    if decision == "進場🔥":

        if breakout:
            buy = f"回踩 {round(resistance,1)}（突破後）"

        elif price >= ma5:
            buy = f"{round(ma5,1)} 附近"

        elif price > ma20:
            buy = f"{round(ma20,1)} 附近"

        else:
            buy = "不建議"

    else:
        buy = "-"

    stop = round(ma20 * 0.98, 1)

    return decision, buy, stop, support, resistance


# ========= 主 =========
def generate():

    now = datetime.now(tz)
    phase = get_phase()

    msg = f"【{now.strftime('%m/%d')} {phase}｜最終完成版】\n\n"

    for name, code in stocks.items():

        twse = get_twse(code)
        yahoo = get_yahoo(code)

        if not twse:
            msg += f"📌 {name}\n→ 無資料\n\n"
            continue

        t_price, t_change, ma5, ma20, closes, volumes = twse

        if "盤中" in phase and yahoo:
            price, change = yahoo
        else:
            price, change = t_price, t_change

        volume = volume_model(volumes, closes)
        trend = trend_model(price, ma5, ma20, closes)

        decision, buy, stop, sup, res = strategy(price, ma5, ma20, closes, volumes)

        msg += f"📌 {name}\n"
        msg += f"→ 現價：{round(price,1)}\n"
        msg += f"→ 漲跌：{round(change,2)}%\n"
        msg += f"→ MA5：{round(ma5,1)}\n"
        msg += f"→ MA20：{round(ma20,1)}\n"
        msg += f"→ 量能：{volume}\n"
        msg += f"→ 趨勢：{trend}\n"
        msg += f"→ 支撐：{round(sup,1)} 壓力：{round(res,1)}\n"
        msg += f"👉 決策：{decision}\n"
        msg += f"🔥 買點：{buy}\n"
        msg += f"🛑 停損：{stop}\n\n"

    return msg


def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    # 防爆長度
    if len(msg) > 4000:
        msg = msg[:4000]

    try:
        r = requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": msg
        })

        print("狀態碼:", r.status_code)
        print("回應:", r.text)

    except Exception as e:
        print("錯誤:", e)

if __name__ == "__main__":
    send(generate())