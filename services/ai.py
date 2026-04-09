import requests
from config import OPENAI_API_KEY

AI_ENABLED = True


# ================================
# 🔥 格式修正（超關鍵）
# ================================
def normalize_ai_output(text):

    if not text:
        return None

    text = text.strip()

    if text.startswith("BUY｜"):
        return text

    if text.startswith("WAIT｜"):
        return text

    if text.startswith("NO｜"):
        return text

    # 🔥 防亂輸出（自動矯正）
    if "BUY" in text:
        return "BUY｜結構偏多"

    if "NO" in text:
        return "NO｜風險偏高"

    return "WAIT｜訊號不足"


# ================================
# 🔥 AI分析（只解釋，不做決策）
# ================================
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

        # ===== 限流 =====
        if r.status_code == 429:
            AI_ENABLED = False
            return fallback_ai(decision), False

        if r.status_code == 200:
            data = r.json()

            # 🔥 更安全解析
            try:
                content_list = data.get("output", [])
                if content_list:
                    content = content_list[0].get("content", [])
                    if content and "text" in content[0]:
                        raw_text = content[0]["text"]
                        text = normalize_ai_output(raw_text)

                        if text:
                            return text, True
            except Exception as e:
                print("parse error:", e)

    except Exception as e:
        print("AI error:", e)

    return fallback_ai(decision), False


# ================================
# 🔥 fallback（語意一致版）
# ================================
def fallback_ai(decision):

    # =============================
    # 🔴 觀望（細分）
    # =============================
    if "觀望" in decision:

        if "未回踩" in decision:
            return "WAIT｜尚未回踩"

        if "追高" in decision:
            return "WAIT｜接近壓力區"

        if "過熱" in decision:
            return "WAIT｜短線過熱"

        if "未到買點" in decision:
            return "WAIT｜尚未到買點"

        if "報酬不足" in decision:
            return "WAIT｜報酬不足"

        if "風險過大" in decision:
            return "WAIT｜停損距離過大"

        if "弱勢" in decision:
            return "WAIT｜結構偏弱"

        return "WAIT｜策略觀望"

    # =============================
    # 🟢 進場
    # =============================
    if "進場🔥" in decision:
        return "BUY｜強勢突破"

    if "進場" in decision:
        return "BUY｜回踩確認"

    # =============================
    # 🟡 試單
    # =============================
    if "試單" in decision:

        if "高風險" in decision:
            return "BUY｜高風險測試"

        return "BUY｜轉強觀察"

    # =============================
    # 🔴 NO（明確不做）
    # =============================
    if "風險" in decision:
        return "NO｜風險偏高"

    if "弱勢" in decision:
        return "NO｜結構偏弱"

    # =============================
    # 預設
    # =============================
    return "WAIT｜訊號不足"