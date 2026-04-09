def ai_analysis(name, price, change, ma5, ma20, volume, trend, decision, buy, stop):

    prompt = f"""
你是頂級短線交易員，請用專業角度快速判斷：

【股票】{name}
【現價】{price}
【漲跌】{change}%
【MA5】{ma5}
【MA20】{ma20}
【量能】{volume}
【趨勢】{trend}
【策略】{decision}
【買點】{buy}
【停損】{stop}

請嚴格輸出（不要廢話）：

1️⃣ 是否該進場（YES / NO / WAIT）
2️⃣ 原因（關鍵一句）
3️⃣ 操作（怎麼買 or 等）

限制：50字內
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
            timeout=12
        )

        if r.status_code == 200:
            data = r.json()

            if "choices" in data:
                text = data["choices"][0]["message"]["content"]

                # ✅ 真AI判斷（有內容才算）
                if text and len(text) > 10:
                    return text.strip(), True

    except Exception as e:
        print("AI error:", e)

    # ===== fallback =====
    if "主升" in trend and "進場" in decision:
        return "YES｜主升段延續｜可小量追", False

    if "突破" in decision:
        return "WAIT｜剛突破｜等回踩確認", False

    if "回檔" in decision:
        return "YES｜支撐附近｜可分批布局", False

    if "轉強" in decision:
        return "YES｜剛轉多頭｜可試單", False

    if "觀望" in decision:
        return "NO｜位置不佳｜等待機會", False

    return "WAIT｜訊號不明｜觀察", False