from supabase import create_client
from datetime import datetime
import pytz

from config import SUPABASE_URL, SUPABASE_KEY

# ===== 初始化 =====
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ===== 時區（可自行改）=====
tz = pytz.timezone("Asia/Taipei")


# ================================
# 🚨 連續虧損檢查（防污染）
# ================================
def get_loss_streak(limit=3):

    res = supabase.table("trades") \
        .select("result") \
        .eq("status", "closed") \
        .order("created_at", desc=True) \
        .limit(limit) \
        .execute()

    streak = 0

    for r in res.data:
        if r["result"] == "loss":
            streak += 1
        else:
            break

    return streak


def can_record():
    streak = get_loss_streak()

    if streak >= 3:
        print(f"🚨 連續虧損 {streak} 次 → 停止記錄")
        return False

    return True


# ================================
# 🧠 記錄交易（核心）
# ================================
def record_trade(
    name,
    decision,
    price,
    buy=None,
    stop=None,
    ma5=None,
    ma20=None,
    volume=None,
    trend=None,
    extra_data=None,
    source="live"
):

    if not can_record():
        return

    now = datetime.now(tz)
    trade_date = now.date().isoformat()   # ⭐交易日

    # 🔒 防重複（同一天同股票）
    existing = supabase.table("trades") \
        .select("id") \
        .eq("stock", name) \
        .eq("trade_date", trade_date) \
        .execute()

    if existing.data:
        print(f"[略過] {name} {trade_date} 已記錄")
        return

    # ===== 組 data（上下文）=====
    data_field = {
        "ma5": ma5,
        "ma20": ma20,
        "volume": volume,
        "trend": trend
    }

    if extra_data:
        data_field.update(extra_data)

    insert_data = {
        "trade_date": trade_date,
        "stock": name,
        "decision": decision,
        "price": price,
        "buy": buy,
        "stop": stop,
        "ma5": ma5,
        "ma20": ma20,
        "volume": volume,
        "trend": trend,
        "data": data_field,
        "status": "pending",   # ⭐關鍵
        "source": source
    }

    supabase.table("trades").insert(insert_data).execute()

    print(f"✅ 已記錄（pending）：{name} | {trade_date}")


# ================================
# 📊 更新結果（進入可用資料）
# ================================
def update_trade_result(name, result, price_after):

    res = supabase.table("trades") \
        .select("id") \
        .eq("stock", name) \
        .eq("status", "pending") \
        .order("created_at", desc=True) \
        .limit(1) \
        .execute()

    if not res.data:
        print("❌ 找不到 pending 資料")
        return

    trade_id = res.data[0]["id"]

    supabase.table("trades") \
        .update({
            "result": result,
            "price_after": price_after,
            "status": "closed"   # ⭐進入乾淨資料
        }) \
        .eq("id", trade_id) \
        .execute()

    print("📊 已更新為 closed（可分析）")


# ================================
# 🔄 手動標記為無效（可選）
# ================================
def mark_invalid(name):

    res = supabase.table("trades") \
        .select("id") \
        .eq("stock", name) \
        .eq("status", "pending") \
        .order("created_at", desc=True) \
        .limit(1) \
        .execute()

    if not res.data:
        print("❌ 找不到資料")
        return

    trade_id = res.data[0]["id"]

    supabase.table("trades") \
        .update({
            "status": "invalid"
        }) \
        .eq("id", trade_id) \
        .execute()

    print("⚠️ 已標記為 invalid")