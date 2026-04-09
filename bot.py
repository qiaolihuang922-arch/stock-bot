import requests
from datetime import datetime, timedelta
import pytz

# ===== 永不移除 =====
TOKEN = "8714533132:AAGEAYs-Q-oZJDwwBwwuB0MPb27mqnDtzxs"
CHAT_ID = "7119676798"

OPENAI_API_KEY = "sk-proj-" + "baPev12uI6bNVR4DNSYwxDHwR8QGUMaWqqb1ozFxHPoJIXDGefi2NAkT6cRu8y1iWSBAj8JgBnT3BlbkFJSfMow23qs6RQmHv3H1FINrbckSgaeAuKhGYcApOtRr-V97pPq6Oc7mnxHPi2NX3XDRLF_VfzEA"

stocks = {
    "緯創": "3231",
    "建準": "2421",
    "智原": "3035"
}

tz = pytz.timezone("Asia/Taipei")
HEADERS = {"User-Agent": "Mozilla/5.0"}


# ===== AI（🔥大幅強化）=====
def ai_analysis(name, price, change, ma5, ma20, volume, trend, decision, buy, stop):

    prompt = f"""
你是專業股票交易員，請根據以下數據做「可執行建議」：

股票：{name}
現價：{price}
漲跌：{change}%
MA5：{ma5}
MA20：{ma20}
量能：{volume}
趨勢：{trend}
決策：{decision}
買點：{buy}
停損：{stop}

輸出要求：
1. 直接給結論（可/不可進場）
2. 說明理由（趨勢+量能）
3. 給操作方式（追/等回檔/觀望）
4. 風險一句

限制：50字內、不要廢話、像真人交易員
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
                "temperature": 0.4
            },
            timeout=15
        )

        if r.status_code == 200:
            content = r.json()["choices"][0]["message"]["content"]
            if content and len(content.strip()) > 5:
                return content.strip()

        print("AI回傳錯誤:", r.text)

    except Exception as e:
        print("AI錯誤:", e)

    # ===== 🔥強化 fallback =====
    if "主升" in decision:
        return "可進場，趨勢強量能配合，順勢操作，勿追高"
    if "觀望" in decision:
        return "不建議進場，位置或結構不佳，等待訊號"
    if price > ma20:
        return "偏多，可回檔布局，避免追價風險"
    return "偏弱觀望，跌破支撐風險高"


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


# ===== TWSE =====
def get_twse(code):
    try:
        rows = []
        now = datetime.now(tz)

        for i in range(3):  # 🔥效能優化（原8→3）
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


# ===== 量能（🔥保留+強化）=====
def volume_model(volumes, closes):
    vol = volumes[-1]
    avg10 = sum(volumes[-10:]) / 10
    ratio = vol / avg10

    # 🔥新增：縮量蓄力
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


# ===== 趨勢（🔥保留+強化）=====
def trend_model(price, ma5, ma20, closes, volumes):

    # 🔥轉強
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


# ===== 策略（🔥保留+強化）=====
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

    # 🔥過熱過濾
    if price > resistance * 1.05:
        return "觀望（過熱區）", "-", "-", "0%"

    # 🔥主升修正（關鍵）
    if volume_strong and momentum and price > ma5 and price > ma20:
        return "進場🔥（主升）", round(price,1), round(structure_low,1), "100%"

    # ===== 原邏輯完整 =====
    if breakout and confirm:
        if closes[-1] <= closes[-2]:
            return "觀望（假突破）", "-", "-", "0%"

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

    # 🔥停損強化
    stop = min(structure_low, buy * 0.97)

    if stop >= buy:
        stop = buy * 0.97

    if (buy - stop) / buy > 0.08:
        return "觀望（風險過大）", "-", "-", "0%"

    # 🔥倉位
    if volume_strong and price > ma20:
        position = "100%"
    elif price > ma20:
        position = "50%"
    else:
        position = "30%"

    return "進場🔥", round(buy,1), round(stop,1), position


# ===== 發送 =====
def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})


# ===== 主 =====
def generate():
    now = datetime.now(tz)
    phase = get_phase()

    msg = f"【{now.strftime('%m/%d')} {phase}｜AI交易系統】\n\n"

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
        decision, buy, stop, position = strategy(price, ma5, ma20, closes, volumes)
        support, resistance = support_resistance(closes)

        ai_text = ai_analysis(name, price, change, ma5, ma20, volume, trend, decision, buy, stop)

        msg += f"{name}\n"
        msg += f"現價：{round(price,1)} | 漲跌：{round(change,2)}%\n"
        msg += f"MA5：{round(ma5,1)} | MA20：{round(ma20,1)}\n"
        msg += f"量能：{volume}\n"
        msg += f"趨勢：{trend}\n"
        msg += f"支撐：{support} 壓力：{resistance}\n"
        msg += f"決策：{decision}\n"
        msg += f"買點：{buy}\n"
        msg += f"停損：{stop}\n"
        msg += f"倉位：{position}\n"
        msg += f"🤖 AI分析：{ai_text}\n\n"

    return msg


if __name__ == "__main__":
    send(generate())