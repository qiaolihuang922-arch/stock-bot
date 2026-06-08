from flask import Flask, request
import requests
import os
import subprocess
import sys
import time
from datetime import datetime
import pytz

app = Flask(__name__)
tz = pytz.timezone("Asia/Taipei")


# ===== 永久防重複 =====
def already_sent(tag):
    today = datetime.now(tz).strftime("%Y%m%d")
    filename = f"sent_{today}.txt"

    if os.path.exists(filename):
        with open(filename, "r") as f:
            tags = f.read().splitlines()
    else:
        tags = []

    return tag in tags


def mark_sent(tag):
    today = datetime.now(tz).strftime("%Y%m%d")
    filename = f"sent_{today}.txt"
    with open(filename, "a") as f:
        f.write(tag + "\n")


def run_market_theme_freshness_preflight():
    lookback = os.getenv("MARKET_THEME_FRESHNESS_LOOKBACK_DAYS", "5")
    safe_write_time = os.getenv("MARKET_THEME_SAFE_WRITE_TIME", "14:00")
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/run_phase3_evidence_automation.py",
            "--freshness-check-only",
            "--freshness-lookback-days",
            lookback,
            "--safe-write-time",
            safe_write_time,
        ],
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )
    if completed.stdout:
        print(completed.stdout, end="" if completed.stdout.endswith("\n") else "\n", flush=True)
    if completed.stderr:
        print(completed.stderr, end="" if completed.stderr.endswith("\n") else "\n", flush=True)
    return completed.returncode


@app.route("/")
def home():
    try:
        if not request.args.get("test"):
            time.sleep(0.3)

        now = datetime.now(tz)
        test_mode = request.args.get("test")

        # 中文註釋：v19.1.3 Render 測試模式優先於假日判斷，方便週末驗證排程與 GitHub Actions 觸發。
        if test_mode == "1":
            tag = now.strftime("%Y%m%d_test_%H%M%S")
            reason = "測試"
        else:
            tag = None
            reason = ""

        if not test_mode and now.weekday() >= 5:
            return "📴 假日"

        hour = now.hour
        minute = now.minute

        # 盤前（不補發）
        if not tag and hour == 8 and 30 <= minute < 40:
            tag = now.strftime("%Y%m%d_pre")
            reason = "盤前"

        # 收盤（允許補發）
        elif not tag and hour == 13 and minute >= 20:
            tag = now.strftime("%Y%m%d_close")
            reason = "收盤"

        # 盤中（不補發）
        elif not tag and 9 <= hour < 13:
            bucket = minute // 10
            tag = f"{now.strftime('%Y%m%d_%H')}_{bucket}"
            reason = "盤中"

        elif not tag:
            return "⏭️ Skip"

        freshness_status = run_market_theme_freshness_preflight()
        freshness_note = ""
        if freshness_status != 0:
            # Freshness is a data-quality preflight. It must not prevent the
            # delivery pipeline from dispatching; the report itself fails
            # closed when evidence is stale or missing.
            freshness_note = f" | freshness warning {freshness_status}"

        if already_sent(tag):
            return f"⏭️ 已發 {tag}"

        token = os.getenv("GITHUB_TOKEN")
        if not token:
            return "❌ No Token"

        # 中文註釋：v19.1.3 改用新的 workflow 檔名，避開 GitHub 舊 workflow ID 無法手動觸發的問題。
        url = "https://api.github.com/repos/qiaolihuang922-arch/stock-bot/actions/workflows/stock-bot-clean.yml/dispatches"

        r = requests.post(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}"
            },
            json={"ref": "main"},
            timeout=10
        )

        if r.status_code != 204:
            return f"❌ GitHub錯誤 {r.status_code}: {r.text[:100]}"

        mark_sent(tag)
        return f"✅ {reason} | {tag} | {now.strftime('%H:%M:%S')}{freshness_note}"

    except Exception as e:
        return f"❌ ERROR: {str(e)}"
