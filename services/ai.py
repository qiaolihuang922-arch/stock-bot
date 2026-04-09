import requests
from config import OPENAI_API_KEY

AI_ENABLED = True


def ai_analysis(name, price, change, ma5, ma20, volume, trend, decision, buy, stop):

    global AI_ENABLED

    prompt = f"""
{name}
現價:{price} 漲跌:{change}%
趨勢:{trend}
策略:{decision}
買點:{buy}
停損:{stop}

YES / NO / WAIT + 原因
"""

    if not AI_ENABLED:
        return fallback_ai(price, ma5, ma20, volume, trend, decision, buy, stop)

    try:
        r = requests.post(
            "https://api.openai.com/v1/responses",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4.1-mini",
                "input": prompt,
                "temperature": 0.3
            },
            timeout=10
        )

        print("AI STATUS:", r.status_code)

        if r.status_code == 429:
            AI_ENABLED = False
            return fallback_ai(price, ma5, ma20, volume, trend, decision, buy, stop)

        if r.status_code == 200:
            data = r.json()

            if "output" in data and data["output"]:
                content = data["output"][0]["content"]

                if content and "text" in content[0]:
                    text = content[0]["text"]

                    if text and len(text.strip()) > 10:
                        return text.strip(), True

    except Exception as e:
        print("AI error:", e)

    return fallback_ai(price, ma5, ma20, volume, trend, decision, buy, stop)


# ===== 🔥 類AI（嚴格版）=====
def fallback_ai(price, ma5, ma20, volume, trend, decision, buy, stop):

    score = 0

    # 趨勢
    if "主升" in trend:
        score += 4
    elif "多頭" in trend:
        score += 2
    elif "轉強" in trend:
        score += 2
    elif "空頭" in trend:
        score -= 4

    # 量能
    if "主升" in volume:
        score += 3
    elif "強放量" in volume:
        score += 2
    elif "出貨" in volume:
        score -= 3

    # 結構
    if price > ma20:
        score += 1
    else:
        score -= 2

    # 策略一致性
    if "進場🔥" in decision:
        score += 2
    elif "進場" in decision:
        score += 1
    elif "觀望" in decision:
        score -= 1

    # 風險
    if buy != "-" and stop != "-":
        risk = (buy - stop) / buy
        if risk > 0.07:
            score -= 3

    # ===== 輸出 =====
    if score >= 7:
        return "YES｜多因子共振｜可進場", False

    elif score >= 4:
        return "WAIT｜條件尚可｜等確認", False

    elif score >= 1:
        return "WAIT｜訊號不足｜觀察", False

    else:
        return "NO｜弱勢｜避免進場", False