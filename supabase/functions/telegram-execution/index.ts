import { serve } from "https://deno.land/std@0.224.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const SUPABASE_URL = Deno.env.get("PROJECT_URL") ?? Deno.env.get("SUPABASE_URL") ?? "";
const SERVICE_ROLE_KEY = Deno.env.get("SERVICE_ROLE_KEY") ?? Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";
const TELEGRAM_BOT_TOKEN = Deno.env.get("TELEGRAM_BOT_TOKEN") ?? "";
const WEBHOOK_SECRET = Deno.env.get("TELEGRAM_WEBHOOK_SECRET") ?? "";
const VERSION = "v19.2.1";

const STOCKS: Record<string, string> = {
  "3231": "緯創",
  "2421": "建準",
  "3035": "智原",
  "2303": "聯電",
  "3481": "群創",
  "2344": "華邦電",
  "2376": "技嘉",
  "2408": "南亞科",
  "2356": "英業達",
  "2324": "仁寶",
  "2301": "光寶科",
  "2337": "旺宏",
};

const NAME_TO_CODE = Object.fromEntries(
  Object.entries(STOCKS).map(([code, name]) => [name, code]),
);

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

function round2(value: number) {
  if (!Number.isFinite(value)) return 0;
  return Math.round((value + Number.EPSILON) * 100) / 100;
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

async function sendMessage(chatId: string, text: string) {
  if (!TELEGRAM_BOT_TOKEN || !chatId) return;

  await fetch(`https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      chat_id: chatId,
      text,
    }),
  });
}

function parseCommand(text: string) {
  const parts = text
    .replace(/＠/g, "@")
    .replace(/，/g, " ")
    .replace(/,/g, " ")
    .replace(/@/g, " ")
    .trim()
    .split(/\s+/)
    .filter(Boolean);

  const verb = parts[0];
  const directStockCode = STOCKS[verb] ? verb : NAME_TO_CODE[verb];

  if (directStockCode) {
    const shares = Number.parseInt(parts[1] ?? "", 10);
    const price = Number.parseFloat(parts[2] ?? "");

    if (Number.isFinite(shares) && shares > 0 && Number.isFinite(price) && price > 0) {
      return {
        stockCode: directStockCode,
        actionCode: "B",
        shares,
        price,
      };
    }

    if (Number.isFinite(shares) && shares > 0) {
      return {
        stockCode: directStockCode,
        actionCode: "S",
        shares,
        price: 0,
      };
    }
  }

  const stockText = parts[1];
  const stockCode = STOCKS[stockText] ? stockText : NAME_TO_CODE[stockText];

  if (!verb || !stockText || !stockCode) {
    return null;
  }

  if (["買", "买", "買入", "买入", "B"].includes(verb)) {
    return {
      stockCode,
      actionCode: "B",
      shares: Number.parseInt(parts[2] ?? "", 10),
      price: Number.parseFloat(parts[3] ?? ""),
    };
  }

  if (["賣", "卖", "賣出", "卖出", "S"].includes(verb)) {
    return {
      stockCode,
      actionCode: "S",
      shares: Number.parseInt(parts[2] ?? "", 10),
      price: 0,
    };
  }

  if (["清倉", "清仓", "C"].includes(verb)) {
    return {
      stockCode,
      actionCode: "C",
      shares: 0,
      price: 0,
    };
  }

  if (["設定", "设定", "設", "设"].includes(verb)) {
    return {
      stockCode,
      actionCode: "SET",
      shares: Number.parseInt(parts[2] ?? "", 10),
      price: Number.parseFloat(parts[3] ?? "0"),
    };
  }

  return null;
}

async function executePositionAction({
  client,
  stockCode,
  actionCode,
  actionShares,
  tradePrice,
  eventId,
  chatId,
  messageId,
  payload,
}: {
  client: ReturnType<typeof createClient>;
  stockCode: string;
  actionCode: string;
  actionShares: number;
  tradePrice: number;
  eventId: string;
  chatId: string;
  messageId: string;
  payload: unknown;
}) {
  const isSet = actionCode === "SET";
  const action = isSet
    ? { eventType: "MANUAL_ADJUST", actionLabel: "設定", sign: 0, realizedDelta: 0 }
    : ACTIONS[actionCode];

  if (!stockCode || !action || !Number.isFinite(actionShares) || actionShares < 0) {
    return { ok: false, status: 400, text: "無效的執行資料", error: "invalid_action_data" };
  }

  if (!isSet && actionCode !== "C" && actionShares <= 0) {
    return { ok: false, status: 400, text: "股數不可為0", error: "invalid_shares" };
  }

  if (action.sign > 0 && tradePrice <= 0) {
    return { ok: false, status: 400, text: "買入需輸入價格，例如：買 緯創 300 149.5", error: "missing_trade_price" };
  }

  if (isSet && actionShares > 0 && tradePrice <= 0) {
    return { ok: false, status: 400, text: "設定持倉需輸入均價，例如：設定 緯創 440 140.92", error: "missing_avg_price" };
  }

  const existing = await client
    .from("position_events")
    .select("id")
    .eq("telegram_callback_id", eventId)
    .maybeSingle();

  if (existing.data) {
    return { ok: true, duplicate: true, text: "已記錄過，不重複執行" };
  }

  const positionResult = await client
    .from("positions")
    .select("*")
    .eq("stock_code", stockCode)
    .single();

  if (positionResult.error || !positionResult.data) {
    return { ok: false, status: 404, text: "找不到持倉資料", error: "position_not_found" };
  }

  const position = positionResult.data;
  const sharesBefore = Number(position.shares ?? 0);

  if (action.sign < 0 && sharesBefore <= 0) {
    return { ok: false, status: 400, text: "目前0股，無法賣出", error: "no_position_to_sell" };
  }

  const sharesDelta = isSet
    ? actionShares - sharesBefore
    : (
      action.sign < 0
        ? -(actionCode === "C" ? sharesBefore : Math.min(actionShares, sharesBefore))
        : actionShares
    );
  const sharesAfter = isSet
    ? actionShares
    : (
      actionCode === "STP"
        ? 0
        : Math.max(sharesBefore + sharesDelta, 0)
    );
  const executionPct = action.sign < 0 && sharesBefore > 0
    ? Math.round(Math.abs(sharesDelta) / sharesBefore * 100)
    : null;
  const avgBefore = round2(Number(position.avg_price ?? 0));
  const avgAfterRaw = isSet
    ? (sharesAfter > 0 ? tradePrice : 0)
    : (
      action.sign > 0
        ? (
          sharesAfter > 0
            ? ((avgBefore * sharesBefore) + (tradePrice * Math.abs(sharesDelta))) / sharesAfter
            : 0
        )
        : (
          sharesAfter > 0
            ? avgBefore
            : 0
        )
    );
  const avgAfter = round2(avgAfterRaw);
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
    avg_price_before: avgBefore,
    avg_price_after: avgAfter,
    realized_profit_delta: action.realizedDelta,
    realized_profit_taken_ratio_after: realizedAfter,
    telegram_callback_id: eventId,
    telegram_chat_id: chatId,
    telegram_message_id: messageId,
    payload,
  };

  const insertResult = await client
    .from("position_events")
    .insert(eventPayload);

  if (insertResult.error) {
    return { ok: false, status: 500, text: "記錄失敗，請稍後重試", error: insertResult.error.message };
  }

  const updateResult = await client
    .from("positions")
    .update({
      shares: sharesAfter,
      avg_price: avgAfter,
      realized_profit_taken_ratio: isSet ? realizedBefore : realizedAfter,
      last_realized_profit_date: action.realizedDelta > 0 ? eventDate : position.last_realized_profit_date,
      status: sharesAfter <= 0 ? "CLOSED" : "ACTIVE",
      source: "telegram",
    })
    .eq("stock_code", stockCode);

  if (updateResult.error) {
    return { ok: false, status: 500, text: "持倉更新失敗，請檢查資料庫", error: updateResult.error.message };
  }

  const pctText = executionPct !== null ? `（${executionPct}%）` : "";
  const avgText = sharesAfter > 0 ? `，均價 ${avgAfter.toFixed(2)}` : "，均價 0.00";
  const text = `${VERSION} 已記錄：${position.stock_name}${action.actionLabel} ${Math.abs(sharesDelta)}股${pctText}，目前 ${sharesAfter}股${avgText}`;

  return {
    ok: true,
    version: VERSION,
    text,
    stock_code: stockCode,
    action: action.actionLabel,
    execution_pct: executionPct,
    shares_before: sharesBefore,
    shares_after: sharesAfter,
    realized_profit_taken_ratio_after: isSet ? realizedBefore : realizedAfter,
  };
}

serve(async (req) => {
  if (req.method !== "POST") {
    return jsonResponse({ ok: false, version: VERSION, error: "method_not_allowed" }, 405);
  }

  if (WEBHOOK_SECRET) {
    const received = req.headers.get("x-telegram-bot-api-secret-token");
    if (received !== WEBHOOK_SECRET) {
      return jsonResponse({ ok: false, version: VERSION, error: "unauthorized" }, 401);
    }
  }

  if (!SUPABASE_URL || !SERVICE_ROLE_KEY) {
    return jsonResponse({ ok: false, version: VERSION, error: "missing_supabase_env" }, 500);
  }

  const update = await req.json();
  const callback = update.callback_query;
  const message = update.message;
  const client = createClient(SUPABASE_URL, SERVICE_ROLE_KEY);

  if (message?.text) {
    const chatId = String(message.chat?.id ?? "");
    const messageId = String(message.message_id ?? "");
    const parsed = parseCommand(String(message.text));

    if (!parsed) {
      return jsonResponse({ ok: true, version: VERSION, ignored: true });
    }

    const result = await executePositionAction({
      client,
      stockCode: parsed.stockCode,
      actionCode: parsed.actionCode,
      actionShares: parsed.shares,
      tradePrice: parsed.price,
      eventId: `msg:${chatId}:${messageId}`,
      chatId,
      messageId,
      payload: message,
    });

    await sendMessage(chatId, result.text ?? "已處理");
    return jsonResponse({ version: VERSION, ...result }, result.ok ? 200 : (result.status ?? 400));
  }

  if (!callback?.id || !callback?.data) {
    return jsonResponse({ ok: true, version: VERSION, ignored: true });
  }

  if (String(callback.data) === "noop") {
    await answerCallback(callback.id, "下方可直接設定持倉");
    return jsonResponse({ ok: true, version: VERSION, noop: true });
  }

  const [prefix, stockCode, actionCode, sharesText, priceToken] = String(callback.data).split("|");
  const action = ACTIONS[actionCode];
  const actionShares = Number.parseInt(sharesText, 10);
  const tradePrice = Number.parseInt(priceToken ?? "0", 10) / 100;

  if (!["exec", "pos"].includes(prefix) || !stockCode || !action || !Number.isFinite(actionShares) || actionShares < 0) {
    await answerCallback(callback.id, "無效的執行資料");
    return jsonResponse({ ok: false, version: VERSION, error: "invalid_callback_data" }, 400);
  }

  if (actionCode !== "C" && actionShares <= 0) {
    await answerCallback(callback.id, "股數不可為0");
    return jsonResponse({ ok: false, version: VERSION, error: "invalid_shares" }, 400);
  }

  if (action.sign > 0 && tradePrice <= 0) {
    await answerCallback(callback.id, "缺少買入價格，請重新產生報文");
    return jsonResponse({ ok: false, version: VERSION, error: "missing_trade_price" }, 400);
  }

  const result = await executePositionAction({
    client,
    stockCode,
    actionCode,
    actionShares,
    tradePrice,
    eventId: callback.id,
    chatId: String(callback.message?.chat?.id ?? ""),
    messageId: String(callback.message?.message_id ?? ""),
    payload: callback,
  });

  await answerCallback(callback.id, result.text ?? "已處理");
  return jsonResponse({ version: VERSION, ...result }, result.ok ? 200 : (result.status ?? 400));
});
