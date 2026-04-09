from flask import Flask
import requests
import os

app = Flask(__name__)

@app.route("/")
def home():
    token = os.getenv("GITHUB_TOKEN")

    url = "https://api.github.com/repos/你的帳號/你的repo/actions/workflows/main.yml/dispatches"

    headers = {
        "Authorization": f"Bearer {token}"
    }

    r = requests.post(url, headers=headers, json={"ref": "main"})

    return f"Trigger: {r.status_code}"