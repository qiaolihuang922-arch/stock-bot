import requests
from config import OPENAI_API_KEY

AI_ENABLED = True


# ===== 🔥 AI分析（只做解釋）=====
def ai_analysis(name, price, change, ma5, ma20, volume, trend, decision, buy, stop):

    global AI_ENABLED

    prompt = f"""
你是交易分析助手，只能解釋策略，不可做決策。

股票：{name}
現價：{price}（{change}%）
MA5：{ma5} MA20：{ma20}
量能：{volume}
趨勢：{trend}

策略決策：
{decision}

請輸出（只能選一種）：

BUY｜解釋為何偏多（20字內）
WAIT｜解釋為何觀望（20字內）
NO｜解釋為何不做（20字內）

⚠️禁止提供：
- 買點
- 停損
- 倉位
- 交易建議
"""

    if not AI_ENABLED:
        return fallback_ai(decision), False

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

        if r.status_code == 429:
            AI_ENABLED = False
            return fallback_ai(decision), False

        if r.status_code == 200:
            data = r.json()

            if "output" in data and data["output"]:
                content = data["output"][0]["content"]

                if content and "text" in content[0]:
                    text = content[0]["text"].strip()

                    # ===== 🔒 格式防護 =====
                    if any(x in text for x in ["BUY｜", "WAIT｜", "NO｜"]):
                        return text, True

    except Exception as e:
        print("AI error:", e)

    return fallback_ai(decision), False


# ===== 🔥 fallback（補語意，但不做決策）=====
def fallback_ai(decision):

    # =============================
    # 🔴 觀望類（細分語意）
    # =============================
    if "觀望" in decision:

        if "未回踩" in decision:
            return "WAIT｜尚未回踩"

        if "追高" in decision:
            return "WAIT｜避免追高"

        if "過熱" in decision:
            return "WAIT｜過熱不追"

        if "未到買點" in decision:
            return "WAIT｜尚未到點"

        if "報酬不足" in decision:
            return "WAIT｜報酬不足"

        if "風險過大" in decision:
            return "WAIT｜風險過高"

        if "弱勢" in decision:
            return "WAIT｜弱勢結構"

        return "WAIT｜策略觀望"

    # =============================
    # 🟢 進場類
    # =============================
    if "進場🔥" in decision:
        return "BUY｜強勢突破"

    if "進場" in decision:
        return "BUY｜回踩確認"

    # =============================
    # 🟡 試單（細分）
    # =============================
    if "試單" in decision:

        if "高風險" in decision:
            return "BUY｜高風險試單"

        return "BUY｜轉強觀察"

    # =============================
    # 🔴 明確不做
    # =============================
    if "風險" in decision:
        return "NO｜風險偏高"

    if "弱勢" in decision:
        return "NO｜結構偏弱"

    # =============================
    # 預設
    # =============================
    return "WAIT｜訊號不足"