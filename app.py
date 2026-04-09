@app.route("/")
def home():
    try:
        time.sleep(1)

        now = datetime.now(tz)

        if now.weekday() >= 5:
            return "📴 假日不執行"

        hour = now.hour
        minute = now.minute

        test_mode = request.args.get("test")

        if test_mode == "1":
            tag = now.strftime("%Y%m%d_test_%H%M%S")

        elif hour == 8 and 30 <= minute < 35:
            tag = now.strftime("%Y%m%d_pre")

        elif 9 <= hour <= 13:
            if not (minute % 10 == 0 and now.second < 10):
                return "⏭️ Skip"
            tag = now.strftime("%Y%m%d_%H%M")

        elif hour == 13 and 20 <= minute < 25:
            tag = now.strftime("%Y%m%d_close")

        else:
            return "⏭️ Skip"

        if already_sent(tag):
            return "⚠️ Already sent"

        token = os.getenv("GITHUB_TOKEN")
        if not token:
            return "❌ GITHUB_TOKEN not found"

        url = "https://api.github.com/repos/qiaolihuang922-arch/stock-bot/actions/workflows/main.yml/dispatches"

        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}"
        }

        data = {
            "ref": "main"
        }

        r = requests.post(url, headers=headers, json=data, timeout=10)

        return f"""
✅ Trigger GitHub: {r.status_code}
🧪 Test Mode: {test_mode}
🕒 Time: {now.strftime("%H:%M")}
📌 Tag: {tag}
📡 Response: {r.text[:100]}
"""

    except Exception as e:
        return f"ERROR:\n{str(e)}"