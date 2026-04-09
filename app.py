from flask import Flask, request
import requests
import os
import time
from datetime import datetime
import pytz

app = Flask(__name__)

# ===== 時區 =====
tz = pytz.timezone("Asia/Taipei")


# =====（可選）防重複機制 =====
sent_cache = set()

def already_sent(tag):
    if tag in sent_cache:
        return True
    sent_cache.add(tag)
    return False


# ===== 主入口 =====
@app.route("/")
def home():
    try:
        # 🔥 避免 Render 冷啟動卡住（測試模式不延遲）
        if not request.args.get("test"):
            time.sleep(0.5)

        now = datetime.now(tz)

        # ===== 假日不跑 =====
        if now.weekday() >= 5:
            return "📴 假日不執行"

        hour = now.hour
        minute = now.minute

        test_mode = request.args.get("test")

        # ===== 測試模式 =====
        if test_mode == "1":
            tag = now.strftime("%Y%m%d_test_%H%M%S")

        # ===== 盤前 =====
        elif hour == 8 and 30 <= minute < 35:
            tag = now.strftime("%Y%m%d_pre")

        # ===== 盤中（每10分鐘）=====
        elif 9 <= hour <= 13:
            if not (minute % 10 == 0 and now.second < 10):
                return "⏭️ Skip"
            tag = now.strftime("%Y%m%d_%H%M")

        # ===== 收盤 =====
        elif hour == 13 and 20 <= minute < 25:
            tag = now.strftime("%Y%m%d_close")

        else:
            return "⏭️ Skip"

        # ===== 防重複 =====
        if already_sent(tag):
            return "⚠️ Already sent"

        # ===== Token =====
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            return "❌ GITHUB_TOKEN not found"

        # ===== GitHub Actions =====
        url = "https://api.github.com/repos/qiaolihuang922-arch/stock-bot/actions/workflows/main.yml/dispatches"

        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}"
        }

        data = {
            "ref": "main"
        }

        r = requests.post(url, headers=headers, json=data, timeout=10)

        return f"""✅ Trigger GitHub: {r.status_code}
🧪 Test Mode: {test_mode}
🕒 Time: {now.strftime("%H:%M")}
📌 Tag: {tag}
📡 Response: {r.text[:100]}"""

    except Exception as e:
        return f"ERROR:\n{str(e)}"