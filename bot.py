
from flask import Flask
import requests
from datetime import datetime, timedelta
import pytz
import time
import os
import traceback

app = Flask(__name__)

# ===== 🔒 永不修改區（AI也不能動）=====
TOKEN = "8714533132:AAGEAYs-Q-oZJDwwBwwuB0MPb27mqnDtzxs"
CHAT_ID = "7119676798"
OPENAI_API_KEY = "sk-proj-xxxx"
# ===== 🔒 END =====


stocks = {
    "緯創": "3231",
    "建準": "2421",
    "智原": "3035"
}

tz = pytz.timezone("Asia/Taipei")
HEADERS = {"User-Agent": "Mozilla/5.0"}


# ===== ✅ 防重複 =====
def already_sent(tag):
    path = f"/tmp/{tag}"
    if os.path.exists(path):
        return True
    open(path, "w").close()
    return False


# ===== 🔥即時行情（完全保留）=====
def get_realtime_price(code):
    try:
        url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_{code}.tw"
        r = requests.get(url, timeout=5).json()

        data = r.get("msgArray")
        if not data:
            return None

        d = data[0]

        z = d.get("z")
        b = d.get("b")
        a = d.get("a")
        y = d.get("y")

        if y in ["-", "", "0"]:
            return None

        prev_close = float(y)
        price = None

        if z not in ["-", "", "0"]:
            price = float(z)
        else:
            try:
                bid = float(b.split("_")[0]) if b else None
                ask = float(a.split("_")[0]) if a else None

                if bid and ask:
                    price = (bid + ask) / 2
                elif bid:
                    price = bid
                elif ask:
                    price = ask
            except:
                return None

        if not price:
            return None

        if price > prev_close * 1.1 or price < prev_close * 0.9:
            return None

        change = (price - prev_close) / prev_close * 100
        return price, change

    except:
        return None


# ===== AI（完全保留）=====
def ai_analysis(name, price, change, ma5, ma20, volume, trend, decision, buy, stop, resistance):

    if "觀望" in decision:
        base = "不建議進場"
    elif "主升" in decision:
        base = "可進場（主升）"
    else:
        base = "可進場"

    prompt = f"""
股票：{name}
現價：{price}
MA20：{ma20}
壓力：{resistance}
量能：{volume}
趨勢：{trend}
決策：{decision}

說明：
是否站上MA20、是否接近壓力、是否可追或等回檔
40字內
"""

    try:
        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4.1-mini",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3
            },
            timeout=10
        )

        if r.status_code == 200:
            text = r.json()["choices"][0]["message"]["content"]
            if text:
                return f"{base}，{text}"

    except:
        pass

    if "觀望" in decision:
        return "不建議進場，位置或結構不佳"
    if price > ma20:
        if abs(price - resistance) / resistance < 0.03:
            return f"站上MA20但接近壓力{resistance}，勿追高"
        return "多頭結構，可回檔布局"
    return "未站上MA20，屬弱勢"


# ===== 時段 =====
def get_phase():
    now = datetime.now(tz)
    if now.hour < 9:
        return "盤前"
    elif 9 <= now.hour <= 13:
        return "盤中🔥"
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


# ===== TWSE（日K）=====
def get_twse(code):
    try:
        rows = []
        now = datetime.now(tz)

        for i in range(6):
            date = now - timedelta(days=30*i)
            url = f"https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=json&date={date.strftime('%Y%m01')}&stockNo={code}"

            try:
                r = requests.get(url, headers=HEADERS, timeout=10).json()
            except:
                continue

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

        rows.sort(key=lambda x: x[0])

        closes = [x[1] for x in rows]
        volumes = [x[2] for x in rows]

        if len(closes) < 20:
            return None

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

    if volumes[-1] < volumes[-2] < volumes[-3] and closes[-1] > sum(closes[-20:]) / 20:
        return "縮量整理（蓄力🔥）"

    vol_trend = volumes[-1] > volumes[-2] > volumes[-3]
    accumulation = sum(volumes[-3:]) > avg10 * 3
    price_up = closes[-1] > closes[-2]

    if ratio > 2:
        level = "爆量"
    elif ratio > 1.5:
        level = "強放量"
    elif ratio > 1.2:
        level = "放量"
    elif ratio < 0.7:
        level = "縮量"
    else:
        level = "正常"

    if price_up and ratio > 1.3 and vol_trend and accumulation:
        return f"{level}（主升✔）"
    if ratio > 1.3 and not price_up:
        return f"{level}（出貨⚠）"
    if price_up and ratio < 1:
        return f"{level}（假突破⚠）"

    return level


# ===== 趨勢 =====
def trend_model(price, ma5, ma20, closes, volumes):

    if closes[-2] < ma20 and price > ma20:
        return "🚀轉強起漲"

    ma20_prev = sum(closes[-21:-1]) / 20
    slope = ma20 - ma20_prev

    recent_high = max(closes[-5:])
    prev_high = max(closes[-10:-5])
    recent_low = min(closes[-5:])
    prev_low = min(closes[-10:-5])

    higher_high = recent_high > prev_high
    higher_low = recent_low > prev_low

    resistance = max(closes[-10:])
    near_res = price >= resistance * 0.97

    if price > ma5 > ma20 and slope > 0 and higher_high and higher_low:
        if price > recent_high * 0.98:
            return "🔥主升段"
        return "👍多頭結構"

    if near_res:
        return "⚠高位震盪"

    if price > ma20 and slope > 0:
        return "多頭"

    if price < ma20 and slope < 0:
        return "空頭"

    return "震盪"


# ===== 支撐壓力 =====
def support_resistance(closes):
    return round(min(closes[-10:]),1), round(max(closes[-10:]),1)


# ===== 策略（完全保留）=====
def strategy(price, ma5, ma20, closes, volumes):
    support, resistance = support_resistance(closes)
    vol = volumes[-1]
    avg10 = sum(volumes[-10:]) / 10

    volume_ok = vol > avg10 * 1.2
    volume_strong = vol > avg10 * 1.5
    momentum = price > closes[-2]

    confirm = sum([volume_ok, momentum, price > ma20]) >= 2
    breakout = price > resistance

    recent_low = min(closes[-5:])
    prev_low = min(closes[-10:-5])
    structure_low = min(recent_low, prev_low)

    if price < ma20 and not volume_strong:
        return "觀望（弱勢）", "-", "-", "0%"

    if price > resistance * 1.05:
        return "觀望（過熱區）", "-", "-", "0%"

    if breakout and confirm:
        if closes[-1] <= closes[-2]:
            return "觀望（假突破）", "-", "-", "0%"

    not_too_high = price < resistance * 1.03
    if volume_strong and momentum and price > ma5 and price > ma20 and not_too_high:
        return "進場🔥（主升）", round(price,1), round(structure_low,1), "100%"

    if price > resistance and vol > avg10 * 1.5:
        buy = price
        stop = max(resistance * 0.97, structure_low)

    elif breakout and confirm:
        buy = price
        stop = max(resistance * 0.97, structure_low)

    elif price >= ma5:
        if price > ma5 * 1.05:
            return "觀望（過高）", "-", "-", "0%"
        buy = min(ma5, support)
        stop = max(ma20 * 0.98, structure_low)

    elif price > ma20:
        buy = ma20
        stop = max(ma20 * 0.97, structure_low)

    else:
        return "觀望", "-", "-", "0%"

    stop = min(structure_low, buy * 0.97)
    stop = min(stop, buy * 0.96)

    if stop >= buy:
        stop = buy * 0.97

    if (buy - stop) / buy > 0.08:
        return "觀望（風險過大）", "-", "-", "0%"

    if volume_strong and price > ma20:
        decision = "進場🔥（主升）"
        position = "100%"
    elif price > ma20:
        decision = "進場"
        position = "50%"
    else:
        decision = "觀望"
        position = "0%"

    return decision, round(buy,1), round(stop,1), position


# ===== 🔥 發送 =====
def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    for i in range(3):
        try:
            r = requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=10)
            if r.status_code == 200:
                return
        except:
            time.sleep(2)


# ===== 主 =====
def generate():
    now = datetime.now(tz)
    phase = get_phase()

    msg = f"【{now.strftime('%m/%d')} {phase}｜AI交易系統】\n\n"

    for name, code in stocks.items():

        twse = get_twse(code)
        yahoo = get_yahoo(code)

        # ✅ 唯一新增：Yahoo備援（不動策略）
        if not twse:
            if yahoo:
                price, change = yahoo
                msg += f"{name}\n現價：{round(price,1)} | 漲跌：{round(change,2)}%\n⚠ Yahoo備援\n\n"
            else:
                msg += f"{name}：無資料\n\n"
            continue

        t_price, t_change, ma5, ma20, closes, volumes = twse

        prev_close = closes[-2]

        use_realtime = False
        if now.hour > 9 or (now.hour == 9 and now.minute >= 2):
            use_realtime = True

        if use_realtime:
            realtime = get_realtime_price(code)
            if realtime:
                price, change = realtime
            elif yahoo:
                price, change = yahoo
            else:
                price = t_price
                change = (price - prev_close) / prev_close * 100
        else:
            price = t_price
            change = t_change

        volume = volume_model(volumes, closes)
        trend = trend_model(price, ma5, ma20, closes, volumes)
        decision, buy, stop, position = strategy(price, ma5, ma20, closes, volumes)
        support, resistance = support_resistance(closes)

        ai_text = ai_analysis(name, price, change, ma5, ma20, volume, trend, decision, buy, stop, resistance)

        msg += f"{name}\n現價：{round(price,1)} | 漲跌：{round(change,2)}%\n"
        msg += f"MA5：{round(ma5,1)} | MA20：{round(ma20,1)}\n"
        msg += f"量能：{volume}\n趨勢：{trend}\n"
        msg += f"支撐：{support} 壓力：{resistance}\n"
        msg += f"決策：{decision}\n買點：{buy}\n停損：{stop}\n倉位：{position}\n"
        msg += f"🤖 AI分析：{ai_text}\n\n"

    return msg


# ===== 🌐 Render入口（修正）=====
@app.route("/")
def home():
    try:
        # ✅ 修正：分鐘級，不會鎖死一天
        tag = datetime.now(tz).strftime("%Y%m%d%H%M")

        if already_sent(tag):
            return "Already sent"

        msg = generate()
        send(msg)

        return "OK"

    except Exception as e:
        err = f"❌ Bot錯誤\n{str(e)}\n\n{traceback.format_exc()}"
        send(err)
        return "ERROR"


# ===== 🚀 GitHub入口 =====
if __name__ == "__main__":
    try:
        tag = datetime.now(tz).strftime("%Y%m%d%H%M")

        if already_sent(tag):
            print("⚠️ 已發送過")
        else:
            msg = generate()
            send(msg)

            if datetime.now(tz).hour == 8:
                send("✅ Bot正常運行")

    except Exception as e:
        err = f"❌ Bot錯誤\n{str(e)}\n\n{traceback.format_exc()}"
        send(err)