import logging
from supabase import create_client
from datetime import datetime
import pytz

from config import SUPABASE_URL, SUPABASE_KEY

# ===== logger =====
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# ===== 初始化 =====
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ===== 時區 =====
tz = pytz.timezone("Asia/Taipei")


# ================================
# 🚨 連續虧損檢查（防污染）
# ================================
def get_loss_streak(limit=3):
    try:
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

        logging.info(f"[loss_streak] {streak}")
        return streak

    except Exception as e:
        logging.error(f"[loss_streak_error] {e}")
        return 0


def can_record():
    streak = get_loss_streak()

    if streak >= 3:
        logging.warning(f"[blocked] 連續虧損 {streak} → 停止記錄")
        return False

    return True


# ================================
# 🔧 型別安全（關鍵防炸）
# ================================
def safe_float(val):
    try:
        if val in ["-", None]:
            return None
        return float(val)
    except:
        return None


def safe_str(val):
    if val in [None, "-"]:
        return None
    return str(val)


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

    # 🔒 決策合法性
    if decision not in ["buy", "sell", "hold"]:
        logging.error(f"[invalid_decision] {decision}")
        return

    if not can_record():
        return

    now = datetime.now(tz)
    trade_date = now.date().isoformat()

    try:
        # 🔒 防重複（核心）
        existing = supabase.table("trades") \
            .select("id") \
            .eq("stock", name) \
            .eq("trade_date", trade_date) \
            .execute()

        if existing.data:
            logging.info(f"[skip] {name} {trade_date} 已存在")
            return

        # ===== 🔥 型別轉換 =====
        price = safe_float(price)
        buy = safe_float(buy)
        stop = safe_float(stop)
        ma5 = safe_float(ma5)
        ma20 = safe_float(ma20)

        volume_str = safe_str(volume)
        trend_str = safe_str(trend)

        # ===== 🔥 data（乾淨版）=====
        data_field = {}

        if ma5 is not None:
            data_field["ma5"] = ma5

        if ma20 is not None:
            data_field["ma20"] = ma20

        if volume_str:
            data_field["volume"] = volume_str

        if trend_str:
            data_field["trend"] = trend_str

        if extra_data:
            data_field.update(extra_data)

        # ===== 🔥 insert =====
        insert_data = {
            "trade_date": trade_date,

            "stock": name,
            "decision": decision,

            "price": price,
            "buy": buy,
            "stop": stop,

            "ma5": ma5,
            "ma20": ma20,
            "volume": volume_str,
            "trend": trend_str,

            "data": data_field,

            "status": "pending",
            "source": source
        }

        supabase.table("trades").insert(insert_data).execute()

        logging.info(f"[recorded] {name} | {decision} | {price}")

    except Exception as e:
        logging.error(f"[record_error] {name} | {e}")


# ================================
# 📊 更新結果
# ================================
def update_trade_result(name, result, price_after):

    if result not in ["win", "loss"]:
        logging.error(f"[invalid_result] {result}")
        return

    price_after = safe_float(price_after)

    try:
        res = supabase.table("trades") \
            .select("id") \
            .eq("stock", name) \
            .eq("status", "pending") \
            .order("created_at", desc=True) \
            .limit(1) \
            .execute()

        if not res.data:
            logging.warning(f"[no_pending] {name}")
            return

        trade_id = res.data[0]["id"]

        supabase.table("trades") \
            .update({
                "result": result,
                "price_after": price_after,
                "status": "closed"
            }) \
            .eq("id", trade_id) \
            .execute()

        logging.info(f"[closed] {name} | {result}")

    except Exception as e:
        logging.error(f"[update_error] {name} | {e}")


# ================================
# 🔄 標記無效
# ================================
def mark_invalid(name):

    try:
        res = supabase.table("trades") \
            .select("id") \
            .eq("stock", name) \
            .eq("status", "pending") \
            .order("created_at", desc=True) \
            .limit(1) \
            .execute()

        if not res.data:
            logging.warning(f"[no_data] {name}")
            return

        trade_id = res.data[0]["id"]

        supabase.table("trades") \
            .update({"status": "invalid"}) \
            .eq("id", trade_id) \
            .execute()

        logging.info(f"[invalid] {name}")

    except Exception as e:
        logging.error(f"[invalid_error] {name} | {e}")