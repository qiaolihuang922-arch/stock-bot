import requests
from config import OPENAI_API_KEY

AI_ENABLED = True


def ai_analysis(name, price, change, ma5, ma20, volume, trend, decision, buy, stop):

    global AI_ENABLED

    prompt = f"""
你是短線交易專家，請根據以下資訊判斷：

{name}
現價:{price} 漲跌:{change}%
MA5:{ma5} MA20:{ma20}
量能:{volume}
趨勢:{trend}
策略:{decision}
買點:{buy}
停損:{stop}

請輸出：
BUY / WAIT / NO + 倉位% + 原因（20字內）
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
                "temperature": 0.2
            },
            timeout=10
        )

        print("AI STATUS:", r.status_code)

        # 👉 限流直接切 fallback（避免卡死）
        if r.status_code == 429:
            AI_ENABLED = False
            return fallback_ai(price, ma5, ma20, volume, trend, decision, buy, stop)

        if r.status_code == 200:
            data = r.json()

            if "output" in data and data["output"]:
                content = data["output"][0]["content"]

                if content and "text" in content[0]:
                    text = content[0]["text"]

                    # 👉 防空、防垃圾回應
                    if text and len(text.strip()) > 10:
                        return text.strip(), True

    except Exception as e:
        print("AI error:", e)

    return fallback_ai(price, ma5, ma20, volume, trend, decision, buy, stop)


# ===== 🔥 統一決策AI（與 strategy 完全同步）=====
def fallback_ai(price, ma5, ma20, volume, trend, decision, buy, stop):

    score = 0

    # ===== 🔥 1. 直接同步 strategy（最重要）=====
    if "進場🔥" in decision:
        return "BUY｜100%｜順勢主升段", False

    if "進場（穩健）" in decision:
        return "BUY｜50%｜趨勢成立回踩", False

    if "試單" in decision:
        return "BUY｜30%｜轉強試單", False

    if "觀望（過熱" in decision or "追高" in decision:
        return "WAIT｜0%｜避免追高", False

    if "弱勢" in decision:
        return "NO｜0%｜弱勢結構", False

    # ===== 🔥 2. 多因子評分（補強判斷）=====

    # 趨勢
    if "主升" in trend:
        score += 4
    elif "轉強" in trend:
        score += 2
    elif "多頭" in trend:
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

    if price > ma5:
        score += 1

    # 位置（避免高位）
    if "高位" in trend:
        score -= 2

    # 風險控制
    if buy != "-" and stop != "-":
        risk = (buy - stop) / buy

        if risk > 0.08:
            score -= 3

        elif risk < 0.03:
            score += 1  # 風險小加分

    # ===== 🔥 3. 最終輸出（嚴格版）=====

    if score >= 6:
        return "BUY｜100%｜多因子共振", False

    elif score >= 4:
        return "BUY｜50%｜條件良好", False

    elif score >= 2:
        return "BUY｜30%｜可試單", False

    elif score >= 0:
        return "WAIT｜0%｜訊號不足", False

    else:
        return "NO｜0%｜避免進場", False