import json
import requests
import time
from config import TOKEN, CHAT_ID

# ================================
# 🔥 notifier.py（v19.1.3｜Telegram 發送層）
# ================================

def send(msg, reply_markup=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    if len(msg) > 3500:
        # 中文註釋：Telegram 長訊息保守截斷，避免整次通知因超長失敗。
        msg = msg[:3500] + "\n\n⚠ 訊息過長已截斷"

    for i in range(3):
        try:
            payload = {
                "chat_id": CHAT_ID,
                "text": msg
            }

            if reply_markup:
                payload["reply_markup"] = json.dumps(
                    reply_markup,
                    ensure_ascii=False
                )

            r = requests.post(url, data=payload, timeout=10)

            if r.status_code == 200:
                print("✅ 發送成功")
                return True
            else:
                print("❌ 發送失敗", r.text)

        except Exception as e:
            print("❌ 發送錯誤", e)

        time.sleep(2)

    # 中文註釋：v19.1.3 Telegram 三次都失敗時回傳 False，讓 GitHub Actions 不再假成功。
    return False


def send_many(messages, reply_markup=None):
    if isinstance(messages, str):
        return send(messages, reply_markup=reply_markup)

    if not messages:
        return False

    for index, message in enumerate(messages):
        markup = reply_markup if index == 0 else None
        if not send(message, reply_markup=markup):
            return False
        time.sleep(0.8)

    return True
