import { serve } from "https://deno.land/std@0.224.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const SUPABASE_URL = Deno.env.get("PROJECT_URL") ?? Deno.env.get("SUPABASE_URL") ?? "";
const SERVICE_ROLE_KEY = Deno.env.get("SERVICE_ROLE_KEY") ?? Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";
const TELEGRAM_BOT_TOKEN = Deno.env.get("TELEGRAM_BOT_TOKEN") ?? "";
const WEBHOOK_SECRET = Deno.env.get("TELEGRAM_WEBHOOK_SECRET") ?? "";

const ACTIONS: Record<string, {
  eventType: string;
  actionLabel: string;
  sign: number;
  realizedDelta: number;
}> = {
  TP50: { eventType: "TAKE_PROFIT", actionLabel: "停利 50%", sign: -1, realizedDelta: 0.5 },
  TP25: { eventType: "TAKE_PROFIT", actionLabel: "停利 25%", sign: -1, realizedDelta: 0.25 },
  R50: { eventType: "REDUCE", actionLabel: "減碼 50%", sign: -1, realizedDelta: 0 },
  R25: { eventType: "REDUCE", actionLabel: "減碼 25%", sign: -1, realizedDelta: 0 },
  STP: { eventType: "STOP", actionLabel: "停損 100%", sign: -1, realizedDelta: 0 },
  A30: { eventType: "ADD", actionLabel: "加碼 30%", sign: 1, realizedDelta: 0 },
  A20: { eventType: "ADD", actionLabel: "加碼 20%", sign: 1, realizedDelta: 0 },
  A10: { eventType: "ADD", actionLabel: "加碼 10%", sign: 1, realizedDelta: 0 },
  B: { eventType: "ADD", actionLabel: "買入", sign: 1, realizedDelta: 0 },
  S: { eventType: "REDUCE", actionLabel: "賣出", sign: -1, realizedDelta: 0 },
  C: { eventType: "STOP", actionLabel: "清倉", sign: -1, realizedDelta: 0 },
};

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json; charset=utf-8" },
  });
}

async function answerCallback(callbackId: string, text: string) {
  if (!TELEGRAM_BOT_TOKEN) return;

  await fetch(`https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/answerCallbackQuery`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      callback_query_id: callbackId,
      text,
      show_alert: false,
    }),
  });
}

serve(async (req) => {
  if (req.method !== "POST") {
    return jsonResponse({ ok: false, error: "method_not_allowed" }, 405);
  }

  if (WEBHOOK_SECRET) {
    const received = req.headers.get("x-telegram-bot-api-secret-token");
    if (received !== WEBHOOK_SECRET) {
      return jsonResponse({ ok: false, error: "unauthorized" }, 401);
    }
  }

  if (!SUPABASE_URL || !SERVICE_ROLE_KEY) {
    return jsonResponse({ ok: false, error: "missing_supabase_env" }, 500);
  }

  const update = await req.json();
  const callback = update.callback_query;

  if (!callback?.id || !callback?.data) {
    return jsonResponse({ ok: true, ignored: true });
  }

  if (String(callback.data) === "noop") {
    await answerCallback(callback.id, "下方可直接設定持倉");
    return jsonResponse({ ok: true, noop: true });
  }

  const [prefix, stockCode, actionCode, sharesText, priceToken] = String(callback.data).split("|");
  const action = ACTIONS[actionCode];
  const actionShares = Number.parseInt(sharesText, 10);
  const tradePrice = Number.parseInt(priceToken ?? "0", 10) / 100;

  if (!["exec", "pos"].includes(prefix) || !stockCode || !action || !Number.isFinite(actionShares) || actionShares < 0) {
    await answerCallback(callback.id, "無效的執行資料");
    return jsonResponse({ ok: false, error: "invalid_callback_data" }, 400);
  }

  if (actionCode !== "C" && actionShares <= 0) {
    await answerCallback(callback.id, "股數不可為0");
    return jsonResponse({ ok: false, error: "invalid_shares" }, 400);
  }

  if (action.sign > 0 && tradePrice <= 0) {
    await answerCallback(callback.id, "缺少買入價格，請重新產生報文");
    return jsonResponse({ ok: false, error: "missing_trade_price" }, 400);
  }

  const client = createClient(SUPABASE_URL, SERVICE_ROLE_KEY);

  const existing = await client
    .from("position_events")
    .select("id")
    .eq("telegram_callback_id", callback.id)
    .maybeSingle();

  if (existing.data) {
    await answerCallback(callback.id, "已記錄過，不重複執行");
    return jsonResponse({ ok: true, duplicate: true });
  }

  const positionResult = await client
    .from("positions")
    .select("*")
    .eq("stock_code", stockCode)
    .single();

  if (positionResult.error || !positionResult.data) {
    await answerCallback(callback.id, "找不到持倉資料");
    return jsonResponse({ ok: false, error: "position_not_found" }, 404);
  }

  const position = positionResult.data;
  const sharesBefore = Number(position.shares ?? 0);
  if (action.sign < 0 && sharesBefore <= 0) {
    await answerCallback(callback.id, "目前0股，無法賣出");
    return jsonResponse({ ok: false, error: "no_position_to_sell" }, 400);
  }

  const sharesDelta = action.sign < 0
    ? -(actionCode === "C" ? sharesBefore : Math.min(actionShares, sharesBefore))
    : actionShares;
  const sharesAfter = actionCode === "STP"
    ? 0
    : Math.max(sharesBefore + sharesDelta, 0);
  const executionPct = action.sign < 0 && sharesBefore > 0
    ? Math.round(Math.abs(sharesDelta) / sharesBefore * 100)
    : null;
  const avgBefore = Number(position.avg_price ?? 0);
  const avgAfter = action.sign > 0
    ? (
      sharesAfter > 0
        ? ((avgBefore * sharesBefore) + (tradePrice * actionShares)) / sharesAfter
        : 0
    )
    : (
      sharesAfter > 0
        ? avgBefore
        : 0
    );
  const realizedBefore = Number(position.realized_profit_taken_ratio ?? 0);
  const realizedAfter = Math.min(realizedBefore + action.realizedDelta, 1);
  const eventDate = new Date().toLocaleDateString("en-CA", {
    timeZone: "Asia/Taipei",
  });

  const eventPayload = {
    stock_code: stockCode,
    stock_name: position.stock_name,
    event_date: eventDate,
    event_type: action.eventType,
    action_label: action.actionLabel,
    shares_delta: sharesDelta,
    shares_before: sharesBefore,
    shares_after: sharesAfter,
    avg_price_before: position.avg_price,
    avg_price_after: avgAfter,
    realized_profit_delta: action.realizedDelta,
    realized_profit_taken_ratio_after: realizedAfter,
    telegram_callback_id: callback.id,
    telegram_chat_id: String(callback.message?.chat?.id ?? ""),
    telegram_message_id: String(callback.message?.message_id ?? ""),
    payload: callback,
  };

  const insertResult = await client
    .from("position_events")
    .insert(eventPayload);

  if (insertResult.error) {
    await answerCallback(callback.id, "記錄失敗，請稍後重試");
    return jsonResponse({ ok: false, error: insertResult.error.message }, 500);
  }

  const updateResult = await client
    .from("positions")
    .update({
      shares: sharesAfter,
      avg_price: avgAfter,
      realized_profit_taken_ratio: realizedAfter,
      last_realized_profit_date: action.realizedDelta > 0 ? eventDate : position.last_realized_profit_date,
      status: sharesAfter <= 0 ? "CLOSED" : "ACTIVE",
      source: "telegram",
    })
    .eq("stock_code", stockCode);

  if (updateResult.error) {
    await answerCallback(callback.id, "持倉更新失敗，請檢查資料庫");
    return jsonResponse({ ok: false, error: updateResult.error.message }, 500);
  }

  const pctText = executionPct !== null ? `（${executionPct}%）` : "";
  await answerCallback(
    callback.id,
    `已記錄：${position.stock_name}${action.actionLabel} ${Math.abs(sharesDelta)}股${pctText}`
  );

  return jsonResponse({
    ok: true,
    stock_code: stockCode,
    action: action.actionLabel,
    execution_pct: executionPct,
    shares_before: sharesBefore,
    shares_after: sharesAfter,
    realized_profit_taken_ratio_after: realizedAfter,
  });
});
