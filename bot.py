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


# ===== 時段 =====
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


# ===== Yahoo =====
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


# ===== TWSE =====
def get_twse(code):
    try:
        rows = []
        now = datetime.now(tz)

        for i in range(8):
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

        if len(rows) < 25:
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


# ===== 量能 =====
def volume_model(volumes, closes):
    vol = volumes[-1]
    avg10 = sum(volumes[-10:]) / 10
    ratio = vol / avg10

    vol_trend = volumes[-1] > volumes[-2] > volumes[-3]
    accumulation = sum(volumes[-3:]) > avg10 * 3
    price_up = closes[-1] > closes[-2]

    if ratio > 1.8:
        level = "爆量"
    elif ratio > 1.3:
        level = "放量"
    elif ratio < 0.7:
        level = "縮量"
    else:
        level = "正常"

    if price_up and ratio > 1.2 and vol_trend and accumulation:
        return f"{level}（主升✔）"
    if ratio > 1.2 and not price_up:
        return f"{level}（出貨⚠）"
    if price_up and ratio < 1:
        return f"{level}（假漲⚠）"

    return level


# ===== 趨勢 =====
def trend_model(price, ma5, ma20, closes, volumes):

    ma20_prev = sum(closes[-21:-1]) / 20
    slope = ma20 - ma20_prev

    recent_high = max(closes[-5:])
    prev_high = max(closes[-10:-5])
    recent_low = min(closes[-5:])
    prev_low = min(closes[-10:-5])

    higher_high = recent_high > prev_high
    higher_low = recent_low > prev_low

    vol = volumes[-1]
    avg10 = sum(volumes[-10:]) / 10
    vol_ratio = vol / avg10

    pullback = (recent_high - price) / recent_high
    resistance = max(closes[-10:])
    near_res = price >= resistance * 0.97

    if price > ma5 > ma20 and slope > 0 and higher_high and higher_low and vol_ratio > 1.2:
        if pullback < 0.03:
            return "🔥主升段"
        elif pullback < 0.08:
            return "🚀加速段"
        else:
            return "⚠過熱"

    if near_res and vol_ratio < 1.2:
        return "⚠高位震盪"

    if price > ma20 and slope > 0:
        return "👍多頭"

    if price < ma20 and slope < 0:
        return "❌空頭"

    return "震盪"


# ===== 支撐壓力 =====
def support_resistance(closes):
    return round(min(closes[-10:]),1), round(max(closes[-10:]),1)


# ===== 策略（唯一修改：停損強化）=====
def strategy(price, ma5, ma20, closes, volumes):

    support, resistance = support_resistance(closes)

    vol = volumes[-1]
    avg10 = sum(volumes[-10:]) / 10
    volume_ok = vol > avg10 * 1.2

    momentum = price > closes[-2]
    trend_ok = price > ma20

    confirm = sum([volume_ok, momentum, trend_ok]) >= 2

    breakout = price > resistance

    # 🔥 新增：結構低點（補強用）
    recent_low = min(closes[-5:])
    prev_low = min(closes[-10:-5])
    structure_low = min(recent_low, prev_low)

    if breakout and confirm:
        stop_old = resistance * 0.97
        stop = max(stop_old, structure_low)
        stop = round(stop, 1)

        if (price - stop) / price > 0.08:
            return "不進場（風險過大）", "-", "-"
        return "進場🔥（突破）", "現價附近", stop

    if price >= ma5:
        if price > ma5 * 1.05:
            return "觀望（過高）", "-", "-"
        stop_old = ma20 * 0.98
        stop = max(stop_old, structure_low)
        stop = round(stop, 1)
        return "進場🔥（回檔）", f"{round(ma5,1)}", stop

    if price > ma20:
        stop_old = ma20 * 0.97
        stop = max(stop_old, structure_low)
        stop = round(stop, 1)
        return "進場🔥（轉強）", f"{round(ma20,1)}", stop

    return "觀望", "-", "-"


# ===== 發送 =====
def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    for i in range(3):
        try:
            r = requests.post(url, data={
                "chat_id": CHAT_ID,
                "text": msg
            }, timeout=10)

            print(r.text)

            if r.status_code == 200 and r.json().get("ok"):
                return
        except:
            pass


# ===== 主 =====
def generate():
    now = datetime.now(tz)
    phase = get_phase()

    msg = f"【{now.strftime('%m/%d')} {phase}｜最終完整交易系統】\n\n"

    for name, code in stocks.items():

        twse = get_twse(code)
        yahoo = get_yahoo(code)

        if not twse:
            msg += f"{name}：無資料\n\n"
            continue

        t_price, t_change, ma5, ma20, closes, volumes = twse

        if "盤中" in phase and yahoo:
            price, change = yahoo
        else:
            price, change = t_price, t_change

        volume = volume_model(volumes, closes)
        trend = trend_model(price, ma5, ma20, closes, volumes)
        decision, buy, stop = strategy(price, ma5, ma20, closes, volumes)
        support, resistance = support_resistance(closes)

        msg += f"{name}\n"
        msg += f"現價：{round(price,1)} | 漲跌：{round(change,2)}%\n"
        msg += f"MA5：{round(ma5,1)} | MA20：{round(ma20,1)}\n"
        msg += f"量能：{volume}\n"
        msg += f"趨勢：{trend}\n"
        msg += f"支撐：{support} 壓力：{resistance}\n"
        msg += f"決策：{decision}\n"
        msg += f"買點：{buy}\n"
        msg += f"停損：{stop}\n\n"

    return msg


if __name__ == "__main__":
    send(generate())