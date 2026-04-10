import requests
import time
from config import OPENAI_API_KEY

AI_ENABLED = True
AI_DISABLED_UNTIL = 0


# ================================
# 🔥 輸出標準化
# ================================
def normalize_ai_output(text):

    if not text:
        return None

    text = text.strip()
    text = text.split("\n")[0].strip()

    return text[:40]


# ================================
# 🔥 fallback（v7升級）
# ================================
def fallback_ai(
    decision,
    decision_type,
    market=None,
    trend=None,
    structure=None,
    volume=None,
    momentum=None,
    breakout_quality=None,
    pullback_type=None,
    rr=0
):

    # ===== BUY =====
    if decision == "BUY":

        if decision_type == "breakout":
            if breakout_quality == "CLEAN":
                reason = "強勢突破，動能充足"
            elif breakout_quality == "WEAK":
                reason = "突破偏弱，需留意"
            else:
                reason = "突破成立"

        elif decision_type == "pullback":
            if pullback_type == "SHALLOW":
                reason = "強勢回踩，延續性高"
            elif pullback_type == "DEEP":
                reason = "回踩過深，風險提高"
            else:
                reason = "回踩支撐"

        else:
            reason = "結構成立"

    # ===== NO_TRADE =====
    elif decision == "NO_TRADE":

        if market == "WEAK":
            reason = "市場偏弱"
        elif volume == "DISTRIBUTION":
            reason = "出貨量風險"
        elif trend == "DOWN":
            reason = "空頭趨勢"
        else:
            reason = "結構不佳"

    # ===== WAIT =====
    else:

        if structure == "WEAK":
            reason = "結構未穩"
        elif momentum == "DECELERATING":
            reason = "動能減弱"
        else:
            reason = "等待觸發條件"

    return {
        "decision": decision,
        "reason": reason
    }


# ================================
# 🔥 AI分析（v7）
# ================================
def ai_analysis(
    name,
    decision,
    decision_type,
    market=None,
    trend=None,
    structure=None,
    volume=None,
    momentum=None,
    breakout_quality=None,
    pullback_type=None,
    rr=0
):

    global AI_ENABLED, AI_DISABLED_UNTIL

    # ===== 冷卻恢復 =====
    if not AI_ENABLED and time.time() > AI_DISABLED_UNTIL:
        AI_ENABLED = True

    # ===== fallback模式 =====
    if not AI_ENABLED:
        return fallback_ai(
            decision, decision_type,
            market, trend, structure,
            volume, momentum,
            breakout_quality, pullback_type,
            rr
        )

    # ===== prompt（v7強化🔥）=====
    prompt = f"""
你是交易決策解釋器（不是分析師）。

請根據以下「已確定的系統判斷」說明原因：

股票:{name}
決策:{decision}
類型:{decision_type}

市場:{market}
趨勢:{trend}
結構:{structure}
量能:{volume}
動能:{momentum}

突破品質:{breakout_quality}
回踩類型:{pullback_type}

RR:{rr}

規則：
- 只能解釋（不可建議）
- 不可新增觀點
- 不可猜測
- 20字內一句話
"""

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
                "temperature": 0.1
            },
            timeout=8
        )

        # ===== 限流 =====
        if r.status_code == 429:
            AI_ENABLED = False
            AI_DISABLED_UNTIL = time.time() + 60
            return fallback_ai(
                decision, decision_type,
                market, trend, structure,
                volume, momentum,
                breakout_quality, pullback_type,
                rr
            )

        if r.status_code != 200:
            return fallback_ai(
                decision, decision_type,
                market, trend, structure,
                volume, momentum,
                breakout_quality, pullback_type,
                rr
            )

        data = r.json()

        text = None

        try:
            if "output_text" in data:
                text = data["output_text"]

            elif "output" in data:
                for item in data["output"]:
                    if "content" in item:
                        for c in item["content"]:
                            if "text" in c:
                                text = c["text"]
                                break

        except Exception as e:
            print("AI parse error:", e)

        text = normalize_ai_output(text)

        if text:
            return {
                "decision": decision,
                "reason": text
            }

    except Exception as e:
        print("AI request error:", e)

    return fallback_ai(
        decision, decision_type,
        market, trend, structure,
        volume, momentum,
        breakout_quality, pullback_type,
        rr
    )