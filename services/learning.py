import logging
from supabase import create_client
from datetime import datetime
import pytz
import uuid

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
# 🔧 debug id
# ================================
def gen_trace_id():
    return str(uuid.uuid4())[:8]


# ================================
# 🚨 連續虧損檢查
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
            if r.get("result") == "loss":
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
# 🔧 型別安全
# ================================
def safe_float(val):
    try:
        if val in ["-", None]:
            return None
        return float(val)
    except Exception as e:
        logging.warning(f"[safe_float_error] {val} | {e}")
        return None


def safe_str(val):
    if val in [None, "-"]:
        return None
    return str(val)


# ================================
# 🧠 記錄交易
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

    trace_id = gen_trace_id()

    logging.info(f"[start_record] {trace_id} | {name}")

    # 🔒 僅允許 buy（符合你系統）
    if decision != "buy":
        logging.error(f"[invalid_decision] {trace_id} | {decision}")
        return

    if not can_record():
        logging.warning(f"[blocked_record] {trace_id}")
        return

    now = datetime.now(tz)
    trade_date = now.date().isoformat()

    try:
        # 🔒 防重複（只看 pending）
        existing = supabase.table("trades") \
            .select("id") \
            .eq("stock", name) \
            .eq("trade_date", trade_date) \
            .eq("status", "pending") \
            .execute()

        if existing.data:
            logging.info(f"[skip] {trace_id} | {name} {trade_date} 已存在")
            return

        # ===== 型別 =====
        price = safe_float(price)
        buy = safe_float(buy)
        stop = safe_float(stop)
        ma5 = safe_float(ma5)
        ma20 = safe_float(ma20)

        volume_str = safe_str(volume)
        trend_str = safe_str(trend)

        logging.info(f"[data_check] {trace_id} | price={price} buy={buy} stop={stop}")

        # ===== data_field（防污染）=====
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
            for k, v in extra_data.items():
                if k not in ["result", "price_after"]:
                    data_field[k] = v

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

        logging.info(f"[insert_ready] {trace_id}")

        res = supabase.table("trades").insert(insert_data).execute()

        if hasattr(res, "data"):
            logging.info(f"[recorded] {trace_id} | {name} | {decision} | {price}")
        else:
            logging.warning(f"[no_response_data] {trace_id}")

    except Exception as e:
        logging.error(f"[record_error] {trace_id} | {name} | {e}")


# ================================
# 📊 更新結果
# ================================
def update_trade_result(name, result, price_after):

    trace_id = gen_trace_id()

    if result not in ["win", "loss"]:
        logging.error(f"[invalid_result] {trace_id} | {result}")
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
            logging.warning(f"[no_pending] {trace_id} | {name}")
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

        logging.info(f"[closed] {trace_id} | {name} | {result}")

    except Exception as e:
        logging.error(f"[update_error] {trace_id} | {name} | {e}")


# ================================
# 🔄 標記無效
# ================================
def mark_invalid(name):

    trace_id = gen_trace_id()

    try:
        res = supabase.table("trades") \
            .select("id") \
            .eq("stock", name) \
            .eq("status", "pending") \
            .order("created_at", desc=True) \
            .limit(1) \
            .execute()

        if not res.data:
            logging.warning(f"[no_data] {trace_id} | {name}")
            return

        trade_id = res.data[0]["id"]

        supabase.table("trades") \
            .update({"status": "invalid"}) \
            .eq("id", trade_id) \
            .execute()

        logging.info(f"[invalid] {trace_id} | {name}")

    except Exception as e:
        logging.error(f"[invalid_error] {trace_id} | {name} | {e}")