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

請輸出：
BUY / WAIT / NO + 倉位% + 原因（簡短）
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


# ===== 🔥 最終交易級AI（完整升級）=====
def fallback_ai(price, ma5, ma20, volume, trend, decision, buy, stop):

    score = 0

    # ===== 🔥 1. 情境優先（最重要） =====

    # 🚀 主升 → 全倉
    if "主升" in trend and "進場" in decision:
        return "BUY｜100%｜主升段延續", False

    # 🚀 轉強突破 → 試單
    if "轉強" in trend and price > ma20:
        return "BUY｜30%｜轉強突破試單", False

    # 📉 高位 → 等
    if "高位" in trend:
        return "WAIT｜0%｜高位震盪避免追高", False

    # ❌ 弱勢
    if "弱勢" in decision or "空頭" in trend:
        return "NO｜0%｜弱勢結構", False

    # ===== 🔥 2. 分數系統（保留+強化） =====

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

    # 策略
    if "進場🔥" in decision:
        score += 2
    elif "進場" in decision:
        score += 1
    elif "試單" in decision:
        score += 1
    elif "觀望" in decision:
        score -= 1

    # 風險控制
    if buy != "-" and stop != "-":
        risk = (buy - stop) / buy
        if risk > 0.07:
            score -= 3

    # ===== 🔥 3. 最終決策（交易級） =====

    if score >= 7:
        return "BUY｜100%｜多因子共振", False

    elif score >= 5:
        return "BUY｜50%｜條件良好", False

    elif score >= 3:
        return "BUY｜30%｜試單觀察", False

    elif score >= 1:
        return "WAIT｜0%｜訊號不足", False

    else:
        return "NO｜0%｜避免進場", False