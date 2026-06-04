import unittest
import ast
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from datetime import datetime

from core import generator
from core.future_watch import (
    build_live_global_event_source,
    build_live_twse_historical_source,
    collect_mops_events,
    collect_global_events,
    format_future_watch_message,
    live_mops_adapter,
)
from presentation import report as presentation_report
from core.signal_snapshot import analyze_ohlcv_snapshot
from services.analysis import TREND_CONTINUATION_DEFAULT_EVIDENCE, strategy


VOL_ATTACK = [1000] * 19 + [1800]
AVAILABLE_STRATEGY_EVIDENCE = {
    "rendered_text": "策略樣本：來源可驗證｜樣本 30｜classification backtest source 可用",
    "structured_status": {
        "status": "available",
        "source": "daily_signal_snapshot",
        "row_count": 30,
        "as_of": "2026-06-02",
        "missing_fields": [],
        "completeness": "complete",
    },
}


def structured_strategy_evidence(status, row_count=0, rendered_text=None, missing_fields=None):
    return {
        "rendered_text": rendered_text,
        "structured_status": {
            "status": status,
            "source": "daily_signal_snapshot",
            "row_count": row_count,
            "as_of": "2026-06-02",
            "missing_fields": missing_fields or [],
            "completeness": "complete" if not missing_fields else "incomplete",
        },
    }


class FakeTable:
    def __init__(self, rows):
        self.rows = rows

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def gte(self, *_args, **_kwargs):
        return self

    def execute(self):
        return SimpleNamespace(data=self.rows)


class FakeClient:
    def __init__(self, signal_rows, price_rows):
        self.signal_rows = signal_rows
        self.price_rows = price_rows

    def table(self, name):
        if name == "daily_signal_snapshot":
            return FakeTable(self.signal_rows)
        if name == "daily_price":
            return FakeTable(self.price_rows)
        return FakeTable([])


def render_payload(closes, holding=None, price=None, change=0):
    snap = analyze_ohlcv_snapshot("3035", "2026-05-22", closes, VOL_ATTACK)
    close = price if price is not None else closes[-1]
    return {
        "result": snap["raw_result"],
        "price": close,
        "change": change,
        "price_source": "realtime",
        "daily_source": "yahoo",
        "stock_code": "3035",
        "ma5": sum(closes[-5:]) / 5,
        "ma20": sum(closes[-20:]) / 20,
        "closes": closes,
        "volumes": VOL_ATTACK,
        "holding": holding,
    }


def trend_continuation_rows():
    rows = []
    for idx in range(26):
        close = 100 + idx
        volume = 1000
        low = close - 0.5
        high = close + 1
        if idx == 24:
            close = 121
            low = 119.2
            volume = 600
        if idx == 25:
            close = 124
            low = 122.8
            high = 125
            volume = 1400
        rows.append({
            "stock_id": "3231",
            "trade_date": f"2026-02-{idx + 1:02d}",
            "open": close - 0.2,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        })
    return rows


def trend_continuation_payload():
    rows = trend_continuation_rows()
    closes = [row["close"] for row in rows]
    volumes = [row["volume"] for row in rows]
    price = closes[-1]
    previous = closes[-2]
    result = strategy(
        price,
        (price - previous) / previous * 100,
        sum(closes[-5:]) / 5,
        sum(closes[-20:]) / 20,
        closes,
        volumes,
        ohlcv_bars=rows,
        trend_continuation_evidence=TREND_CONTINUATION_DEFAULT_EVIDENCE,
        stock_id="3231",
    )
    return {
        "result": result,
        "price": price,
        "change": (price - previous) / previous * 100,
        "price_source": "realtime",
        "daily_source": "yahoo",
        "stock_code": "3231",
        "ma5": sum(closes[-5:]) / 5,
        "ma20": sum(closes[-20:]) / 20,
        "closes": closes,
        "volumes": volumes,
        "volume_ratio": round(volumes[-1] / (sum(volumes[-10:]) / 10), 2),
        "ohlcv": rows[-1],
        "holding": None,
    }


def summary_message(messages):
    return next(
        message for message in messages
        if f"｜{generator.VERSION}】" in message and "🧾" in message
    )


def position_message(messages):
    return next(message for message in messages if "【持倉標的】" in message)


def unheld_message(messages):
    return next(message for message in messages if "【未持倉標的】" in message)


def detail_message(messages):
    return next(message for message in messages if message.startswith("【Details Backup】"))


def evidence_message(messages):
    return next(message for message in messages if "🧾" in message)


def future_watch_message(messages):
    return next(message for message in messages if "【未來30日關注】" in message)


def card_block(message, title):
    return title + message.split(title, 1)[1].split("\n\n", 1)[0]


def first_line_for_prefix(message, prefix):
    return next(line for line in message.splitlines() if line.startswith(prefix))


FORBIDDEN_SHORT_EVIDENCE_TERMS = [
    "source:",
    "status:",
    "use:",
    "limit:",
    "conflict:",
    "derived",
    "missing-source",
    "insufficient-data",
    "unresolved-conflict",
    "not-used",
    "position_events",
    "db_table",
    "source_of_truth",
    "latest_trade_date",
    "lookback_range",
    "Evidence Compact",
    "Report：as_of",
    "候選：price/source",
    "source gaps fail closed",
    "Source：漏斗 count",
    "production DB",
    "production_db",
    "runtime",
    "classification backtest",
    "source-of-truth",
    "source_status",
    "market_theme_confirmed_evidence",
    "daily_signal_snapshot",
    "as_of",
    "fail-closed",
]

ROOT = Path(__file__).resolve().parents[1]
IMPORT_GATE_SCAN_PATHS = [
    ROOT / "presentation",
    ROOT / "services",
    ROOT / "core",
    ROOT / "main.py",
    ROOT / "app.py",
]
IMPORT_GATE_EXCLUDED_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "build",
    "dist",
}
PRESENTATION_FORBIDDEN_IMPORT_PREFIXES = {
    "services.signal_store",
    "services.daily_snapshot_store.record_daily_snapshots",
    "services.strategy_evidence",
}
PRESENTATION_FORBIDDEN_SYMBOLS = {
    "record_daily_signals",
    "record_daily_snapshots",
    "record_strategy_evidence",
    "get_supabase_client",
}
PRESENTATION_BRIDGE_ALLOWLIST = {
    ("core/generator.py", "presentation.report"),
}
PRESENTATION_INTEGRATION_ALLOWLIST = {
    "services/notifier.py",
}


def _iter_import_gate_python_files():
    for scan_path in IMPORT_GATE_SCAN_PATHS:
        if scan_path.is_file():
            yield scan_path
            continue
        for path in scan_path.rglob("*.py"):
            relative_parts = path.relative_to(ROOT).parts
            if IMPORT_GATE_EXCLUDED_PARTS.intersection(relative_parts):
                continue
            yield path


def _import_targets(node):
    if isinstance(node, ast.Import):
        for alias in node.names:
            yield alias.name
        return

    if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
        module = node.module
        for alias in node.names:
            if alias.name == "*":
                yield module
            elif module == "presentation":
                yield f"presentation.{alias.name}"
            else:
                yield f"{module}.{alias.name}"


def _presentation_import_is_forbidden(target):
    if target in PRESENTATION_FORBIDDEN_IMPORT_PREFIXES:
        return True
    if any(target.startswith(f"{prefix}.") for prefix in PRESENTATION_FORBIDDEN_IMPORT_PREFIXES):
        return True
    symbol = target.rsplit(".", 1)[-1]
    return symbol in PRESENTATION_FORBIDDEN_SYMBOLS and target.startswith("services.")


def _find_import_boundary_violations(sources_by_relative_path):
    violations = []
    for relative_path, source in sources_by_relative_path.items():
        tree = ast.parse(source, filename=relative_path)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Import, ast.ImportFrom)):
                continue
            for target in _import_targets(node):
                if relative_path.startswith("presentation/"):
                    if _presentation_import_is_forbidden(target):
                        violations.append(
                            (
                                "presentation_db_or_strategy_writer_import",
                                relative_path,
                                target,
                            )
                        )
                    continue

                if not (
                    relative_path.startswith("services/")
                    or relative_path.startswith("core/")
                ):
                    continue
                if not target.startswith("presentation"):
                    continue
                if relative_path in PRESENTATION_INTEGRATION_ALLOWLIST:
                    continue
                if any(
                    relative_path == allowed_path
                    and (target == allowed_target or target.startswith(f"{allowed_target}."))
                    for allowed_path, allowed_target in PRESENTATION_BRIDGE_ALLOWLIST
                ):
                    continue
                violations.append(
                    (
                        "strategy_or_service_imports_presentation",
                        relative_path,
                        target,
                    )
                )
    return violations


def _format_import_boundary_violations(violations):
    return "\n".join(
        "Import boundary violation: {rule}\nfile={path}\nimport={target}".format(
            rule=rule,
            path=path,
            target=target,
        )
        for rule, path, target in violations
    )


class GeneratorReportTest(unittest.TestCase):
    def test_v20_4_38_rr_wait_card_reason_and_backtest_summary_readability(self):
        buyable = self.evidence_payload(confidence=82, decision="BUY", action=0.1, rr=1.8, distance=0.5)
        buyable["stock_code"] = "2421"
        buyable["backtest_context"] = {"sample": 38, "reference": "高", "win_rate": 58, "avg_return": -0.8}

        rr_wait = self.evidence_payload(confidence=66, decision="WAIT", action=0, rr=0.98, distance=2)
        rr_wait["stock_code"] = "2301"
        rr_wait["volume_ratio"] = 0.86
        rr_wait["backtest_context"] = {"sample": 38, "reference": "高", "win_rate": 45, "avg_return": -0.7}
        rr_wait["result"].update({
            "trade_state": "LATE_ENTRY",
            "market_grade": "B",
        })

        with patch.object(generator, "market_theme_summary_evidence", return_value=self.confirmed_market_evidence()):
            messages = generator.formatTelegramMessages(
                {"建準": buyable, "光寶科": rr_wait},
                "",
                None,
                None,
                {"trade_date": "2026-06-04"},
                datetime(2026, 6, 4),
                strategy_evidence_summary=structured_strategy_evidence("available", row_count=30),
                report_phase="盤中",
            )

        summary = summary_message(messages)
        unheld = unheld_message(messages)
        liteon_card = card_block(unheld, "【光寶科 2301】")

        self.assertIn("【06/04 盤中｜v20.4.47】", summary)
        self.assertIn("【光寶科 2301】👀 等RR修復｜RR不足", liteon_card)
        self.assertIn("數據：RR 0.98｜不適用（RR不足）｜原因：RR不足，等待RR修復｜V 0.86x", liteon_card)
        self.assertNotIn("證據：資料不足", liteon_card)
        self.assertIn("回測（建準）：樣本38｜參考度高｜3日勝率58%｜相對-0.8%｜偏弱", summary)
        self.assertNotIn("回測（光寶科）", summary)
        self.assertIn("僅追蹤 1（等RR修復）", summary)

    def test_trend_continuation_official_report_has_separate_small_buy_bucket(self):
        payload = trend_continuation_payload()
        self.assertEqual(payload["result"]["decision_type"], "trend_continuation")

        messages = generator.formatTelegramMessages(
            {"智原": payload},
            "",
            "智原",
            90,
            "市場偏強",
            datetime(2026, 6, 3, 10, 0),
            strategy_evidence_summary=AVAILABLE_STRATEGY_EVIDENCE,
            report_phase="盤中",
        )
        summary = summary_message(messages)
        unheld = unheld_message(messages)
        evidence = evidence_message(messages)
        rendered = "\n\n".join(messages)
        context = generator.build_report_context(
            {"智原": payload},
            "市場偏強",
            datetime(2026, 6, 3, 10, 0),
            strategy_evidence_summary=AVAILABLE_STRATEGY_EVIDENCE,
            report_phase="盤中",
        )

        self.assertIn("趨勢延續買入 1 檔小倉", summary)
        self.assertIn("新倉建議 1", summary)
        self.assertIn("未持倉 1（趨勢延續1/僅追蹤0/淘汰0）", evidence)
        self.assertIn("趨勢延續 1", rendered)
        self.assertIn("【智原 3231】🟢 趨勢延續買入｜小倉", unheld)
        self.assertIn("買點：趨勢延續買入｜小倉 <=15%｜回測 55% 勝 / +2.26%", unheld)
        self.assertIn("依據：回測 55% 勝 / +2.26%，回踩站回 ma5/ma10 後放量確認", unheld)
        self.assertIn("倉位：<=15%", unheld)
        self.assertIn("止損：回踩低點下方；形態失效即出", unheld)
        self.assertIn("持有：對齊 5 日 edge", unheld)
        self.assertNotIn("資料依據", evidence)
        self.assertTrue(context["manifest"])
        self.assertEqual(context["source_status"]["strategy_sample"], "available")
        self.assertTrue(context["evidence_status"]["strategy_sample"])
        self.assertNotIn("策略樣本來源可驗證，只作輔助參考，不新增買點", rendered)
        self.assertNotIn("未持倉資料只支持分類觀察，不支持直接進場", rendered)

    def test_v20_4_43_trend_continuation_rr_hard_gate_fails_closed_official_report(self):
        payload = trend_continuation_payload()
        payload["result"]["rr"] = 0.8
        payload["result"]["risk_reward"] = 0.8
        self.assertEqual(payload["result"]["decision_type"], "trend_continuation")

        messages = generator.formatTelegramMessages(
            {"智原": payload},
            "",
            "智原",
            90,
            "市場偏強",
            datetime(2026, 6, 3, 10, 0),
            strategy_evidence_summary=AVAILABLE_STRATEGY_EVIDENCE,
            report_phase="盤中",
        )
        context = generator.build_report_context(
            {"智原": payload},
            "市場偏強",
            datetime(2026, 6, 3, 10, 0),
            strategy_evidence_summary=AVAILABLE_STRATEGY_EVIDENCE,
            report_phase="盤中",
        )

        summary = summary_message(messages)
        unheld = unheld_message(messages)
        evidence = evidence_message(messages)
        card = card_block(unheld, "【智原 3231】")
        rendered = "\n\n".join(messages)
        judgment = context["stock_judgments"]["智原"]

        self.assertEqual(judgment["eligibility_state"], "blocked")
        self.assertIn("unresolved RR不足", judgment["blocking_reasons"])
        self.assertNotIn("新倉建議 1", summary)
        self.assertNotIn("趨勢延續買入 1 檔小倉", summary)
        self.assertNotIn("可買", summary)
        self.assertNotIn("未持倉 1（趨勢延續1/僅追蹤0/淘汰0）", evidence)
        self.assertNotIn("【智原 3231】🟢 趨勢延續買入｜小倉", rendered)
        self.assertNotIn("買點：趨勢延續買入｜小倉 <=15%", card)
        self.assertIn("【智原 3231】👀 等RR修復｜RR不足", card)
        self.assertIn("卡關主因：RR不足", card)
        self.assertIn("量化差距：RR 0.8｜需>=1.5｜差0.7", card)
        self.assertIn("解鎖：風險報酬比修復到 >=1.5", card)
        self.assertNotIn("決策證據：來源可追溯", card)
        self.assertIn("僅追蹤 1（等RR修復）", summary)

    def test_load_stock_signal_passes_trend_continuation_ohlcv_and_evidence(self):
        rows = trend_continuation_rows()
        closes = [row["close"] for row in rows]
        volumes = [row["volume"] for row in rows]
        daily = (
            closes[-1],
            (closes[-1] - closes[-2]) / closes[-2] * 100,
            sum(closes[-5:]) / 5,
            sum(closes[-20:]) / 20,
            closes,
            volumes,
            rows,
        )

        with patch.object(generator, "load_report_daily_kline", return_value=(daily, "yahoo", None)), \
             patch.object(generator, "get_realtime_price", return_value=None), \
             patch.object(generator, "get_yahoo", return_value=None), \
             patch.object(generator, "get_last_ohlcv", return_value=rows[-1]):
            name, data, decision, error = generator.load_stock_signal("智原", "3231")

        self.assertEqual(name, "智原")
        self.assertIsNone(error)
        self.assertEqual(decision, "BUY")
        self.assertEqual(data["result"]["decision_type"], "trend_continuation")
        self.assertEqual(data["ohlcv_bars"], rows)

    def test_load_stock_signal_fails_closed_without_trend_continuation_source_rows(self):
        rows = trend_continuation_rows()
        closes = [row["close"] for row in rows]
        volumes = [row["volume"] for row in rows]
        daily = (
            closes[-1],
            (closes[-1] - closes[-2]) / closes[-2] * 100,
            sum(closes[-5:]) / 5,
            sum(closes[-20:]) / 20,
            closes,
            volumes,
        )

        with patch.object(generator, "load_report_daily_kline", return_value=(daily, "yahoo", None)), \
             patch.object(generator, "get_realtime_price", return_value=None), \
             patch.object(generator, "get_yahoo", return_value=None), \
             patch.object(generator, "get_last_ohlcv", return_value=rows[-1]):
            _name, data, _decision, error = generator.load_stock_signal("智原", "3231")

        self.assertIsNone(error)
        self.assertNotEqual(data["result"]["decision_type"], "trend_continuation")
        self.assertIsNone(data["ohlcv_bars"])

    def test_import_boundary_gate_for_strategy_presentation_and_service_layers(self):
        sources_by_relative_path = {
            str(path.relative_to(ROOT)): path.read_text(encoding="utf-8")
            for path in _iter_import_gate_python_files()
        }

        violations = _find_import_boundary_violations(sources_by_relative_path)

        self.assertFalse(violations, _format_import_boundary_violations(violations))

    def test_import_boundary_gate_reports_offending_file_import_and_rule(self):
        sources_by_relative_path = {
            "presentation/fake_report.py": (
                "from services.strategy_evidence import record_strategy_evidence\n"
            ),
            "presentation/fake_signal.py": (
                "from services.signal_store import record_daily_signals\n"
            ),
            "presentation/fake_snapshot.py": (
                "from services.daily_snapshot_store import record_daily_snapshots\n"
            ),
            "presentation/fake_client.py": (
                "from services.strategy_evidence import get_supabase_client\n"
            ),
            "services/fake_service.py": "from presentation import report\n",
            "core/fake_strategy.py": "import presentation.report\n",
            "core/generator.py": "from presentation.report import render_telegram_messages\n",
            "main.py": "from presentation import report\n",
            "services/notifier.py": "from presentation import report\n",
        }

        violations = _find_import_boundary_violations(sources_by_relative_path)
        formatted = _format_import_boundary_violations(violations)

        self.assertIn(
            "Import boundary violation: presentation_db_or_strategy_writer_import",
            formatted,
        )
        self.assertIn("file=presentation/fake_report.py", formatted)
        self.assertIn("import=services.strategy_evidence.record_strategy_evidence", formatted)
        self.assertIn("file=presentation/fake_signal.py", formatted)
        self.assertIn("import=services.signal_store.record_daily_signals", formatted)
        self.assertIn("file=presentation/fake_snapshot.py", formatted)
        self.assertIn("import=services.daily_snapshot_store.record_daily_snapshots", formatted)
        self.assertIn("file=presentation/fake_client.py", formatted)
        self.assertIn("import=services.strategy_evidence.get_supabase_client", formatted)
        self.assertIn(
            "Import boundary violation: strategy_or_service_imports_presentation",
            formatted,
        )
        self.assertIn("file=services/fake_service.py", formatted)
        self.assertIn("import=presentation.report", formatted)
        self.assertIn("file=core/fake_strategy.py", formatted)
        self.assertEqual(6, len(violations), formatted)

    def test_presentation_report_module_has_no_storage_or_evidence_write_imports(self):
        source = Path(presentation_report.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        forbidden_names = {
            "record_daily_signals",
            "record_strategy_evidence",
            "get_supabase_client",
            "record_daily_snapshots",
            "create_table",
            "alter_table",
            "add_column",
        }
        imported_names = set()
        called_names = set()
        mutated_argument_roots = set()

        class Visitor(ast.NodeVisitor):
            def visit_ImportFrom(self, node):
                for alias in node.names:
                    imported_names.add(alias.asname or alias.name)

            def visit_Import(self, node):
                for alias in node.names:
                    imported_names.add(alias.asname or alias.name.split(".")[0])

            def visit_Call(self, node):
                func = node.func
                if isinstance(func, ast.Name):
                    called_names.add(func.id)
                elif isinstance(func, ast.Attribute):
                    called_names.add(func.attr)
                self.generic_visit(node)

            def visit_Assign(self, node):
                for target in node.targets:
                    self._collect_mutated_root(target)
                self.generic_visit(node)

            def visit_AugAssign(self, node):
                self._collect_mutated_root(node.target)
                self.generic_visit(node)

            def visit_Delete(self, node):
                for target in node.targets:
                    self._collect_mutated_root(target)
                self.generic_visit(node)

            def _collect_mutated_root(self, target):
                root = target
                while isinstance(root, (ast.Subscript, ast.Attribute)):
                    root = root.value
                if isinstance(root, ast.Name) and root.id in {"results_map", "result", "holding_decision"}:
                    mutated_argument_roots.add(root.id)

        Visitor().visit(tree)

        self.assertTrue(callable(presentation_report.render_telegram_messages))
        self.assertFalse(imported_names & forbidden_names)
        self.assertFalse(called_names & forbidden_names)
        self.assertFalse(mutated_argument_roots)

    def test_generate_report_fails_closed_when_holdings_source_missing(self):
        with patch.object(generator, "load_positions", return_value={}), \
             patch.object(generator, "load_today_position_events", return_value={}), \
             patch.object(generator, "get_position_store_warning", return_value="持倉來源缺失：missing-source"), \
             patch.object(generator, "get_market_phase", return_value="盤中"):
            messages, reply_markup = generator.generate_report()

        summary = summary_message(messages)
        detail = messages[-1]
        self.assertIsNone(reply_markup)
        self.assertEqual(len(messages), 3)
        self.assertIn("【持倉標的】", messages[0])
        self.assertIn("【未持倉標的】", messages[1])
        self.assertIn("｜v20.4.47】", summary)
        self.assertIn(f"🧾 {generator.VERSION} 簡報", summary)
        self.assertIn("新倉：無有效進場", summary)
        self.assertNotIn("資料依據", summary)
        for term in FORBIDDEN_SHORT_EVIDENCE_TERMS:
            self.assertNotIn(term, summary)
        self.assertNotIn("今日可買", summary)
        self.assertNotIn("confirmed", summary)
        self.assertNotIn("資料依據", "\n\n".join(messages))

    def test_generate_report_fails_closed_when_position_events_source_errors(self):
        holdings = {
            "英業達": {
                "shares": 100,
                "avg_price": 52.15,
                "realized_profit_taken_ratio": 0,
                "realized_profit_taken_date": None,
            }
        }
        event_warning = "今日交易事件讀取失敗：source-error (events unavailable)"
        with patch.object(generator, "load_positions", return_value=holdings), \
             patch.object(
                 generator,
                 "load_today_position_events",
                 return_value={
                     "_source_status": "unavailable",
                     "available": False,
                     "today_events_known": False,
                     "warning": event_warning,
                 },
             ), \
             patch.object(generator, "get_position_store_warning", return_value=event_warning), \
             patch.object(generator, "get_market_phase", return_value="盤中"):
            messages, reply_markup = generator.generate_report()

        summary = summary_message(messages)
        self.assertIsNone(reply_markup)
        self.assertIn("新倉：無有效進場", summary)
        self.assertNotIn("資料依據", summary)
        for term in FORBIDDEN_SHORT_EVIDENCE_TERMS:
            self.assertNotIn(term, summary)
        self.assertNotIn("今日 無", summary)
        self.assertNotIn("今日可買", summary)

    def breakout_distance_payload(
        self,
        distance,
        *,
        holding=False,
        include_result_distance=True,
        data_distance="missing",
    ):
        result = {
            "decision": "WAIT",
            "action": 0,
            "rr": 1.2,
            "heat_state": "NORMAL",
            "trade_state": "WAIT",
            "structure_phase": "BREAKOUT_CONFIRM",
            "price_behavior": "NORMAL",
            "market_grade": "B",
            "volume_state": "NORMAL",
            "volume_price_state": "NORMAL",
            "structure_state": "NORMAL",
            "entry_quality": "B",
            "confidence_score": 70,
        }
        if include_result_distance:
            result["breakout_distance"] = distance

        payload = {
            "stock_code": "0000",
            "price": 100,
            "change": 0,
            "price_source": "realtime",
            "daily_source": "yahoo",
            "result": result,
            "holding": {"shares": 10, "avg_price": 100} if holding else None,
            "structure_score": 4,
            "volume_ratio": 1.0,
        }
        if holding:
            payload["holding_decision"] = {
                "action": "續抱",
                "level": "HOLD_WATCH",
                "note": "觀察",
                "warning_price": 95,
                "hard_stop_price": 90,
            }
        if data_distance != "missing":
            payload["breakout_distance"] = data_distance
        return payload

    def score_source_report_context(self, name, score_status, *, report_phase="盤中"):
        def field(suffix, status):
            return {"field_name": f"stock.{name}.{suffix}", "source_status": status}

        return {
            "report_context": {"report_phase": report_phase, "version": generator.VERSION},
            "evidence_manifest": [
                field("price", "available"),
                field("daily_ohlcv", "available"),
                field("rr", "derived"),
                field("score", score_status),
                field("volume", "derived"),
                field("position", "available"),
                field("execution_memory", "available"),
                field("risk", "derived"),
                {"field_name": "evidence.strategy_sample", "source_status": "available"},
            ],
            "source_status_summary": {
                "price": "available",
                "position": "available",
                "strategy_sample": "available",
                "market_theme": "available",
                "funnel": "derived",
            },
        }

    def score_gate_payload(self, *, holding=False):
        payload = {
            "stock_code": "0000",
            "price": 100.0,
            "change": 1.2,
            "price_source": "realtime",
            "daily_source": "yahoo",
            "result": {
                "decision": "BUY",
                "action": 0.1,
                "rr": 2.1,
                "heat_state": "NORMAL",
                "trade_state": "READY",
                "structure_phase": "BREAKOUT_CONFIRM",
                "price_behavior": "NORMAL",
                "market_grade": "A",
                "volume_state": "STRONG",
                "volume_price_state": "EXPANSION",
                "structure_state": "STRONG",
                "entry_quality": "A",
                "confidence_score": 88,
                "strength": 95,
            },
            "holding": {"shares": 10, "avg_price": 96.0} if holding else None,
            "structure_score": 5,
            "volume_ratio": 1.5,
            "closes": [90, 91, 92, 93, 94, 95, 96, 97, 98, 100],
            "volumes": [1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900],
        }
        if holding:
            payload["holding_decision"] = {
                "action": "續抱",
                "level": "HOLD_WATCH",
                "note": "觀察",
                "warning_price": 95,
                "hard_stop_price": 90,
            }
        return payload

    def test_score_source_insufficient_holding_card_hides_s_number_and_strength_text(self):
        card = generator.formatTelegramPositionCard(
            "TEST",
            self.score_gate_payload(holding=True),
            report_context=self.score_source_report_context("TEST", "insufficient-data"),
        )

        self.assertIn("數據：不適用（既有持倉）", card)
        self.assertIn("盤面：強弱證據不足｜待確認", card)
        self.assertIn("價格：100.0（+1.20%）", card)
        self.assertNotIn("S 5/5", card)
        self.assertNotIn("突破確認", card)
        self.assertNotIn("極強", card)

    def test_score_source_error_unheld_card_hides_s_number_without_hiding_price_or_rr(self):
        card = generator.formatTelegramUnheldCard(
            "TEST",
            self.score_gate_payload(),
            report_phase="盤中",
            report_context=self.score_source_report_context("TEST", "source-error"),
        )

        self.assertIn("數據：RR 2.1｜S 不可用｜V 1.5x", card)
        self.assertIn("盤面：強弱證據不足｜待確認", card)
        self.assertIn("價格：100.0（+1.20%）", card)
        self.assertNotIn("S 5/5", card)
        self.assertNotIn("突破確認", card)
        self.assertNotIn("極強", card)

    def test_score_source_available_and_derived_cards_keep_existing_score_and_strength_text(self):
        for holding, status, formatter in [
            (True, "derived", generator.formatTelegramPositionCard),
            (False, "available", generator.formatTelegramUnheldCard),
        ]:
            with self.subTest(holding=holding, status=status):
                payload = self.score_gate_payload(holding=holding)
                context = self.score_source_report_context("TEST", status)
                if holding:
                    card = formatter("TEST", payload, report_context=context)
                else:
                    card = formatter("TEST", payload, report_phase="盤中", report_context=context)

                self.assertIn("盤面：突破確認", card)
                if holding:
                    self.assertIn("數據：不適用（既有持倉）", card)
                    self.assertNotIn("S 5/5", card)
                else:
                    self.assertIn("S 5/5", card)
                    self.assertIn("RR 2.1", card)
                self.assertNotIn("S 證據不足", card)
                self.assertNotIn("強弱證據不足", card)

    def test_available_score_weak_or_far_market_line_does_not_show_extreme_strength(self):
        payload = self.score_gate_payload()
        payload["result"].update({
            "decision": "WAIT",
            "structure_phase": "WEAK",
            "breakout_distance": 7,
            "market_grade": "A",
        })

        card = generator.formatTelegramUnheldCard(
            "TEST",
            payload,
            report_phase="盤中",
            report_context=self.score_source_report_context("TEST", "available"),
        )

        self.assertIn("盤面：弱勢｜待確認｜攻擊量｜遠離突破（7%）", card)
        self.assertNotIn("弱勢｜極強", card)
        self.assertNotIn("遠離突破｜極強", card)

    def test_v20_2_1_holding_card_always_shows_breakout_distance_when_available(self):
        cases = [
            (-1, "已突破，位於突破區上方"),
            (0, "臨界突破（0%）"),
            (2, "接近突破（2%）"),
            (7, "遠離突破（7%）"),
        ]

        for distance, expected in cases:
            with self.subTest(distance=distance):
                card = generator.formatTelegramPositionCard(
                    "範例股",
                    self.breakout_distance_payload(distance, holding=True),
                )

                self.assertIn(f"盤面：突破確認｜偏強｜普通｜{expected}", card)

    def test_v20_2_1_unheld_card_always_shows_breakout_distance_when_available(self):
        cases = [
            (-1, "已突破，位於突破區上方"),
            (0, "臨界突破（0%）"),
            (2, "接近突破（2%）"),
            (7, "遠離突破（7%）"),
        ]

        for distance, expected in cases:
            with self.subTest(distance=distance):
                card = generator.formatTelegramUnheldCard(
                    "範例股",
                    self.breakout_distance_payload(distance),
                    report_phase="盤中",
                )

                self.assertIn(f"盤面：突破確認｜偏強｜普通｜{expected}", card)

    def test_v20_2_1_card_breakout_distance_falls_back_to_result_and_omits_missing(self):
        holding_card = generator.formatTelegramPositionCard(
            "範例股",
            self.breakout_distance_payload(2, holding=True, data_distance=None),
        )
        unheld_card = generator.formatTelegramUnheldCard(
            "範例股",
            self.breakout_distance_payload(7, data_distance=None),
            report_phase="盤中",
        )

        self.assertIn("盤面：突破確認｜偏強｜普通｜接近突破（2%）", holding_card)
        self.assertIn("盤面：突破確認｜偏強｜普通｜遠離突破（7%）", unheld_card)

        for holding in [True, False]:
            with self.subTest(holding=holding):
                payload = self.breakout_distance_payload(
                    None,
                    holding=holding,
                    include_result_distance=False,
                )
                if holding:
                    card = generator.formatTelegramPositionCard("範例股", payload)
                else:
                    card = generator.formatTelegramUnheldCard(
                        "範例股",
                        payload,
                        report_phase="盤中",
                    )

                self.assertIn("盤面：突破確認｜偏強｜普通", card)
                self.assertNotIn("（0%）", card)
                self.assertNotIn("None%", card)
                self.assertNotIn("（）", card)

    def test_limit_lock_conclusion_is_not_overridden_by_rr(self):
        result = {
            "decision": "BUY",
            "action": 1,
            "price_behavior": "LIMIT_LOCK",
            "trade_state": "EXTENDED",
            "heat_state": "HOT",
            "rr": 0.5,
            "market_grade": "A+",
        }

        self.assertEqual(generator.entry_conclusion(result), "漲停鎖價，不追高")

    def test_blocked_entry_does_not_get_validation_context(self):
        result = {
            "decision": "BUY",
            "action": 1,
            "price_behavior": "NORMAL",
            "trade_state": "LATE_ENTRY",
            "heat_state": "NORMAL",
            "rr": 0.5,
            "market_grade": "A+",
            "stock_code": "2421",
        }
        signal_rows = [
            {
                "stock_id": "2421",
                "trade_date": "2026-05-01",
                "version": "v19.1",
                "pattern": "BREAKOUT_CONFIRM",
                "market_state": "A+",
                "rr": 0.5,
                "heat_level": 0,
                "action": "BUY",
                "reasons": ["RR不足"],
                "is_tradeable": False,
                "is_best_candidate": False,
            }
        ]
        price_rows = [
            {"stock_id": "2421", "trade_date": "2026-05-01", "close": 100},
            {"stock_id": "2421", "trade_date": "2026-05-02", "close": 102},
            {"stock_id": "2421", "trade_date": "2026-05-03", "close": 103},
            {"stock_id": "2421", "trade_date": "2026-05-04", "close": 104},
        ]

        with patch.object(generator, "get_supabase_client", return_value=FakeClient(signal_rows, price_rows)):
            context = generator.load_backtest_context({
                "建準": {
                    "result": result,
                    "stock_code": "2421",
                    "holding": None,
                }
            })

        self.assertEqual(context, {})

    def test_holding_add_uses_basis_label(self):
        payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119],
            {"shares": 50, "avg_price": 118},
            price=119,
            change=1.4,
        )

        report = generator.render_stock("智原", payload)

        self.assertIn("【智原 3035】", report)
        self.assertIn("├─ 決策：加碼 10% 5股｜小幅轉強", report)
        self.assertIn("├─ 倉控：目標 55股｜分批加碼", report)
        self.assertIn("├─ 依據：小幅轉強、RR達標、信心達標", report)
        self.assertNotIn("├─ 阻斷：條件成立", report)

    def test_generate_reports_data_source_errors_when_all_quotes_fail(self):
        with patch.object(generator, "stocks", {"測試": "1234"}), \
             patch.object(generator, "load_positions", return_value={}), \
             patch.object(generator, "load_today_position_events", return_value={}), \
             patch.object(generator, "get_position_store_warning", return_value=None), \
             patch.object(generator, "get_twse", return_value=None), \
             patch.object(generator, "get_yahoo_history", return_value=None), \
             patch.object(generator, "get_last_error", return_value="twse: DNS failed"):
            report = generator.generate()

        self.assertIn("⚠ 無有效數據：行情來源未返回可用日線", report)
        self.assertIn("測試(1234) twse: DNS failed", report)

    def test_load_stock_signal_uses_yahoo_daily_fallback_when_twse_fails(self):
        closes = [
            100, 101, 102, 103, 104,
            105, 106, 107, 108, 109,
            110, 111, 112, 113, 114,
            115, 116, 117, 118, 119
        ]
        volumes = VOL_ATTACK
        daily = (
            119,
            1.4,
            sum(closes[-5:]) / 5,
            sum(closes[-20:]) / 20,
            closes,
            volumes
        )

        with patch.object(generator, "get_twse", return_value=None), \
             patch.object(generator, "get_yahoo_history", return_value=daily), \
             patch.object(generator, "get_last_error", return_value="twse: timeout"), \
             patch.object(generator, "get_realtime_price", return_value=None), \
             patch.object(generator, "get_yahoo", return_value=None), \
             patch.object(generator, "get_last_ohlcv", return_value={"source": "yahoo"}):
            name, data, decision, error = generator.load_stock_signal("測試", "1234")

        self.assertEqual(name, "測試")
        self.assertIsNone(error)
        self.assertIsNotNone(data)
        self.assertEqual(data["daily_source"], "yahoo")
        self.assertEqual(data["price_source"], "yahoo")
        self.assertIsNotNone(decision)

    def test_load_stock_signal_uses_minimal_yahoo_daily_without_twse_when_sufficient(self):
        closes = [
            100, 101, 102, 103, 104,
            105, 106, 107, 108, 109,
            110, 111, 112, 113, 114,
            115, 116, 117, 118, 119
        ]
        daily = (
            119,
            1.4,
            sum(closes[-5:]) / 5,
            sum(closes[-20:]) / 20,
            closes,
            VOL_ATTACK
        )

        with patch.object(generator, "get_yahoo_history", return_value=daily) as yahoo_history, \
             patch.object(generator, "get_twse") as twse, \
             patch.object(generator, "get_realtime_price", return_value=(120, 1.7)), \
             patch.object(generator, "get_yahoo") as yahoo_quote, \
             patch.object(generator, "get_last_ohlcv", return_value={"source": "yahoo"}):
            name, data, decision, error = generator.load_stock_signal("測試", "1234")

        self.assertEqual(name, "測試")
        self.assertIsNone(error)
        self.assertIsNotNone(data)
        self.assertEqual(data["daily_source"], "yahoo")
        self.assertEqual(data["price_source"], "realtime")
        self.assertIsNotNone(decision)
        yahoo_history.assert_called_once_with("1234", months=1, min_rows=generator.REPORT_DAILY_MIN_ROWS)
        twse.assert_not_called()
        yahoo_quote.assert_not_called()

    def test_load_report_daily_kline_falls_back_to_limited_twse_window(self):
        closes = [
            100, 101, 102, 103, 104,
            105, 106, 107, 108, 109,
            110, 111, 112, 113, 114,
            115, 116, 117, 118, 119
        ]
        daily = (
            119,
            1.4,
            sum(closes[-5:]) / 5,
            sum(closes[-20:]) / 20,
            closes,
            VOL_ATTACK
        )

        with patch.object(generator, "get_yahoo_history", return_value=None) as yahoo_history, \
             patch.object(generator, "get_twse", return_value=daily) as twse, \
             patch.object(generator, "get_last_error", return_value="yahoo_daily: timeout"):
            result, source, error = generator.load_report_daily_kline("1234")

        self.assertEqual(result, daily)
        self.assertEqual(source, "twse")
        self.assertIsNone(error)
        yahoo_history.assert_called_once_with("1234", months=1, min_rows=generator.REPORT_DAILY_MIN_ROWS)
        twse.assert_called_once_with(
            "1234",
            months=1,
            min_rows=generator.REPORT_DAILY_MIN_ROWS,
            max_months=2
        )

    def test_hidden_rr_is_not_listed_as_advantage(self):
        result = {
            "decision": "NO_TRADE",
            "structure_phase": "WEAK_REBOUND",
            "price_behavior": "WEAK_REBOUND",
            "market_grade": "D",
            "structure_state": "NORMAL",
            "volume_price_state": "COILING",
            "volume_state": "WEAK",
            "rr": 2.5,
        }

        self.assertTrue(generator.should_hide_rr(result))
        self.assertNotIn("RR足夠", generator.entry_advantages(result))

    def test_backtest_context_uses_pattern_volume_and_position(self):
        result = {
            "decision": "BUY",
            "action": 1,
            "structure_phase": "BREAKOUT_CONFIRM",
            "price_behavior": "NORMAL",
            "trade_state": "LATE_ENTRY",
            "heat_state": "NORMAL",
            "rr": 0.5,
            "market_grade": "A+",
            "breakout_distance": -1,
        }
        signal_rows = []
        price_rows = []

        for day in range(1, 10):
            price_rows.append({
                "stock_id": "2421",
                "trade_date": f"2026-05-{day:02d}",
                "close": 100 + day,
            })

        for day in range(1, 7):
            signal_rows.append({
                "stock_id": "2421",
                "trade_date": f"2026-05-{day:02d}",
                "version": "v19.1",
                "pattern": "BREAKOUT_CONFIRM",
                "market_state": "A+",
                "structure_state": "STRONG",
                "position_state": "BREAKOUT",
                "volume_ratio": 2.5,
                "rr": 0.5,
                "heat_level": 0,
                "action": "BUY",
                "reasons": ["RR不足"],
                "is_tradeable": False,
                "is_best_candidate": False,
            })

        with patch.object(generator, "get_supabase_client", return_value=FakeClient(signal_rows, price_rows)):
            context = generator.load_backtest_context({
                "建準": {
                    "result": result,
                    "stock_code": "2421",
                    "volumes": [100] * 9 + [300],
                    "holding": None,
                }
            })

        self.assertIn("建準", context)
        self.assertEqual(context["建準"]["label"], "同型 突破確認/爆量/已突破")
        self.assertEqual(context["建準"]["scope"], "同型")
        self.assertEqual(context["建準"]["setup"], "突破確認/爆量/已突破")
        self.assertEqual(context["建準"]["sample"], 6)
        self.assertTrue(
            context["建準"]["action"] == "維持不買"
            or "不追價" in context["建準"]["action"]
            or "依今日阻斷" in context["建準"]["action"]
        )

    def test_setup_bucket_falls_back_to_price_position(self):
        closes = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 122]
        result = {
            "structure_phase": "BREAKOUT_CONFIRM",
        }
        bucket = generator.setup_bucket_from_result(
            result,
            {
                "price": 122,
                "closes": closes,
                "volumes": [100] * 9 + [300],
            }
        )

        self.assertEqual(bucket, ("BREAKOUT_CONFIRM", "爆量", "BREAKOUT"))

    def test_market_forward_return_uses_same_day_universe(self):
        lookup = {
            "1111": [
                (generator.parse_trade_date("2026-05-01"), 100),
                (generator.parse_trade_date("2026-05-02"), 100),
                (generator.parse_trade_date("2026-05-03"), 100),
                (generator.parse_trade_date("2026-05-04"), 110),
            ],
            "2222": [
                (generator.parse_trade_date("2026-05-01"), 100),
                (generator.parse_trade_date("2026-05-02"), 100),
                (generator.parse_trade_date("2026-05-03"), 100),
                (generator.parse_trade_date("2026-05-04"), 90),
            ],
        }

        self.assertEqual(
            generator.market_forward_return(
                lookup,
                generator.parse_trade_date("2026-05-01"),
                3
            ),
            0
        )

    def test_holding_context_uses_holding_wording(self):
        result = {
            "decision": "WAIT",
            "action": 0,
            "structure_phase": "BREAKOUT_CONFIRM",
            "price_behavior": "NORMAL",
            "trade_state": "TRADEABLE",
            "heat_state": "NORMAL",
            "rr": 1.2,
            "market_grade": "A+",
            "breakout_distance": -1,
            "_holding_decision": {
                "level": "HOLD"
            }
        }
        signal_rows = []
        price_rows = []

        for stock_id in ["3035", "9999"]:
            for day in range(1, 10):
                price_rows.append({
                    "stock_id": stock_id,
                    "trade_date": f"2026-05-{day:02d}",
                    "close": 100 + day,
                })

        for day in range(1, 7):
            signal_rows.append({
                "stock_id": "3035",
                "trade_date": f"2026-05-{day:02d}",
                "version": "v19.1",
                "pattern": "BREAKOUT_CONFIRM",
                "market_state": "A+",
                "structure_state": "NORMAL",
                "position_state": "BREAKOUT",
                "volume_ratio": 1.4,
                "rr": 1.2,
                "heat_level": 0,
                "action": "WAIT",
                "reasons": ["突破確認"],
                "is_tradeable": False,
                "is_best_candidate": False,
            })

        with patch.object(generator, "get_supabase_client", return_value=FakeClient(signal_rows, price_rows)):
            context = generator.load_backtest_context({
                "智原": {
                    "result": result,
                    "stock_code": "3035",
                    "volumes": [100] * 9 + [150],
                    "holding": {
                        "shares": 50,
                        "avg_price": 100
                    },
                }
            })

        self.assertIn("智原", context)
        self.assertEqual(context["智原"]["label"], "持倉同型 突破確認/放量/已突破")
        self.assertTrue(
            "續抱" in context["智原"]["action"]
            or "持倉規則" in context["智原"]["action"]
        )

    def test_backtest_context_renders_data_and_explanation(self):
        text = generator.render_backtest_context({
            "version": "v19.1",
            "scope": "同型",
            "setup": "突破確認/爆量/已突破",
            "sample": 15,
            "win_rate": 60,
            "avg_return": 1.8,
            "metric": "3日相對股票池",
            "verdict": "歷史偏強，但今日阻斷仍有效",
            "action": "列觀察，不追價"
        })

        self.assertIn(
            "├─ 策略樣本 / 分類回測：未持倉｜突破確認/爆量/已突破\n"
            "├─ 樣本：15 筆；觀察口徑：v19.1 classification backtest\n"
            "├─ 解讀：3日勝率 60%｜相對 +1.8%｜偏強但阻斷有效；只作歷史分類參考",
            text
        )

    def test_backtest_context_renders_negative_relative_result(self):
        text = generator.render_backtest_context({
            "version": "v19.1",
            "scope": "持倉同型",
            "setup": "突破確認/放量/已突破",
            "sample": 35,
            "win_rate": 46,
            "avg_return": -0.6,
            "metric": "3日相對股票池",
            "verdict": "加碼樣本偏弱",
            "action": "依風控續抱，不加碼"
        })

        self.assertIn(
            "├─ 策略樣本 / 分類回測：持倉｜突破確認/放量/已突破\n"
            "├─ 樣本：35 筆；觀察口徑：v19.1 classification backtest\n"
            "├─ 解讀：3日勝率 46%｜相對 -0.6%｜加碼偏弱，不加碼；只作歷史分類參考",
            text
        )

    def test_backtest_context_fails_closed_when_sample_insufficient(self):
        text = generator.render_backtest_context({
            "version": "v19.1",
            "scope": "同型",
            "setup": "突破確認/爆量/已突破",
            "sample": 8,
            "win_rate": 50,
            "avg_return": 0.3,
            "metric": "3日相對股票池",
            "verdict": "樣本中性",
            "action": "依今日條件",
        })

        self.assertIn("├─ 策略樣本 / 分類回測：不可用", text)
        self.assertIn("原因：classification backtest 樣本不足（有效樣本 8）", text)
        self.assertIn("個股決策只看既有買點與風控", text)

    def test_execution_reply_markup_uses_compact_callback(self):
        markup = generator.execution_reply_markup({
            "英業達": {
                "stock_code": "2356",
                "price": 65.4,
                "holding": {
                    "shares": 550,
                    "avg_price": 52.15
                },
                "holding_decision": {
                    "level": "TAKE_PROFIT_25",
                    "action": "停利 25%",
                    "shares": 138
                },
                "result": {}
            }
        })

        self.assertEqual(
            markup["inline_keyboard"],
            [
                [{"text": "輸入買入：3231 300 149.5", "callback_data": "noop"}],
                [{"text": "輸入賣出：3231 500", "callback_data": "noop"}],
                [{"text": "輸入清倉：清倉 3231", "callback_data": "noop"}],
                [{"text": "輸入設定：設定 3231 440 140.92", "callback_data": "noop"}],
            ]
        )

    def test_telegram_messages_use_summary_cards_and_detail(self):
        holding_payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119],
            {"shares": 50, "avg_price": 118},
            price=119,
            change=1.4,
        )
        watch_payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119],
            None,
            price=119,
            change=1.4,
        )
        watch_payload["stock_code"] = "2421"
        watch_payload["result"]["rr"] = 0.5
        watch_payload["result"]["trade_state"] = "LATE_ENTRY"

        generator.render_stock("智原", holding_payload)
        generator.render_stock("建準", watch_payload)
        messages = generator.formatTelegramMessages(
            {
                "智原": holding_payload,
                "建準": watch_payload,
            },
            "FULL DETAIL",
            None,
            None,
            "⏳ 觀望",
            datetime(2026, 5, 25),
            report_phase="盤中",
        )

        self.assertEqual(len(messages), 3)
        self.assertIn("【持倉標的】", position_message(messages))
        self.assertIn("倉位：50股", position_message(messages))
        self.assertIn("【未持倉標的】", unheld_message(messages))
        self.assertIn("【建準 2421】👀 等RR修復｜RR不足", unheld_message(messages))
        self.assertIn("買點：不買，等RR達標", unheld_message(messages))
        self.assertIn("盤中觸發：RR修復至達標，不追高", unheld_message(messages))
        self.assertNotIn("策略樣本：不可用，本次不納入判斷", unheld_message(messages))
        self.assertIn("市場：進攻偏熱 R3｜執行動作 1（加碼10）｜今日新建倉 0｜持倉風控 1｜未持倉 1（僅追蹤1/淘汰0）", summary_message(messages))
        self.assertNotIn("📌 持倉：智原", summary_message(messages))
        self.assertIn("原因：持倉多數依風控處理，新倉無有效進場。", summary_message(messages))
        self.assertIn("風險：持倉：hard_stop 永不豁免", summary_message(messages))
        self.assertIn("✅ 今日盤中交易執行", summary_message(messages))
        self.assertIn("智原 加碼10（加碼後守警戒價，量價未延續則停止加碼）", summary_message(messages))
        self.assertIn("未持倉 1 檔僅追蹤，等觸發，不列入今日盤中交易執行", summary_message(messages))
        self.assertNotIn("建準｜等RR修復｜不追價，等RR達標", summary_message(messages))
        self.assertIn("未持倉漏斗（非執行）：", summary_message(messages))
        self.assertIn("未持倉 1｜可買 0｜不可追高觀察 0（不可買）｜僅追蹤 1（等RR修復）｜淘汰 0", summary_message(messages))
        self.assertIn("不可追高觀察 0（不可買）", summary_message(messages))
        self.assertIn("僅追蹤 1（等RR修復）", summary_message(messages))
        self.assertIn("📎 詳情索引：持倉 智原｜交易執行 1｜僅追蹤 1", summary_message(messages))
        self.assertNotIn("完整詳情備份", "\n".join(messages))

    def test_v20_4_47_future_30d_watch_optional_fourth_message_official_list(self):
        holding_payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119],
            {"shares": 50, "avg_price": 118},
            price=119,
            change=1.4,
        )
        holding_payload["stock_code"] = "2301"
        watch_payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119],
            None,
            price=119,
            change=1.4,
        )
        watch_payload["stock_code"] = "2421"
        watch_payload["result"]["rr"] = 0.5
        watch_payload["result"]["trade_state"] = "LATE_ENTRY"
        mops_calls = []

        def mops_adapter(params):
            mops_calls.append(dict(params))
            if params["co_id"] == "2301" and params["TYPEK"] == "sii" and params["year"] == 115 and params["month"] == "06":
                return {
                    "rows": [{
                        "date": "2026-06-20",
                        "co_id": "2301",
                        "name": "光寶科",
                        "event": "法人說明會",
                    }]
                }
            return {"rows": []}

        global_events = [
            {"date": "2026-06-25", "event": "BEA GDP third estimate", "impact": "通膨/利率", "source": "BEA"},
            {"date": "2026-06-10", "event": "美國 CPI（May 2026）", "impact": "通膨/利率", "source": "BLS"},
            {"date": "2026/06/10-11", "event": "ECB 利率會議/記者會", "impact": "利率/匯率", "source": "ECB"},
            {"date": "2026/06/15-16", "event": "日本央行 BOJ 利率會議", "impact": "利率/匯率", "source": "BOJ"},
            {"date": "2026-06-16-17", "event": "Fed FOMC 利率決策/SEP", "impact": "利率/匯率", "source": "Fed"},
            {"date": "2026-06-18", "event": "BoE MPC", "impact": "利率/匯率", "source": "BoE"},
            {"date": "2026/06/15-2026/06/17", "event": "G7 Evian", "impact": "政治風險", "source": "G7"},
            {"date": "2026/06/99-100", "event": "Invalid official row", "impact": "政治風險", "source": "Official"},
        ]
        messages = generator.formatTelegramMessages(
            {
                "光寶科": holding_payload,
                "建準": watch_payload,
            },
            "FULL DETAIL",
            None,
            None,
            "⏳ 觀望",
            datetime(2026, 6, 4),
            report_phase="盤中",
            future_watch_sources={
                "historical_source": {
                    "samples": [{
                        "date": "2020-03-12",
                        "event": "疫情急跌時間線",
                        "similarity": 0.84,
                        "matched_features": ["跌幅擴大", "量能放大", "市場廣度轉弱", "遠離均線"],
                    }]
                },
                "mops_adapter": mops_adapter,
                "global_event_source": global_events,
            },
        )

        self.assertEqual(len(messages), 4)
        self.assertIn("【持倉標的】", messages[0])
        self.assertIn("【未持倉標的】", messages[1])
        self.assertIs(messages[2], summary_message(messages))
        self.assertIn(f"【06/04 未來30日關注｜{generator.VERSION}】", messages[3])
        self.assertIn("【未來30日關注】", messages[3])
        self.assertNotIn("未來30日台股影響事件", summary_message(messages))
        self.assertNotIn("未來30日法說會", summary_message(messages))
        self.assertLess(messages[3].index("歷史類比"), messages[3].index("未來30日法說會"))
        self.assertLess(messages[3].index("未來30日法說會"), messages[3].index("未來30日台股影響事件"))
        self.assertNotIn("\n全球事件\n", messages[3])
        self.assertNotIn("\n法說會提醒\n", messages[3])
        self.assertIn("歷史類比：03/12 疫情急跌時間線｜相似度 84%｜相似：跌幅擴大、量能放大、市場廣度轉弱｜類比不是預測", messages[3])
        self.assertNotIn("即將崩盤", messages[3])
        self.assertNotIn("重演", messages[3])
        self.assertIn("06/20 2301 光寶科｜法人說明會｜關注原因：持倉｜source=MOPS", messages[3])
        self.assertNotIn("0-count", messages[3])
        self.assertNotIn("查無資料", messages[3].split("未來30日台股影響事件", 1)[0])
        global_lines = [
            line for line in messages[3].splitlines()
            if "｜影響面：" in line and "來源：" in line
        ]
        self.assertEqual(len(global_lines), 5)
        self.assertEqual(global_lines[0], "06/10-11 ECB 利率會議/記者會｜影響面：利率/匯率｜來源：ECB官方")
        self.assertIn("06/10 美國 CPI（May 2026）｜影響面：通膨/利率｜來源：BLS官方", global_lines[1])
        self.assertIn("06/15-16 日本央行 BOJ 利率會議｜影響面：利率/匯率｜來源：BOJ官方", global_lines)
        self.assertIn("06/16-17 Fed FOMC 利率決策/SEP｜影響面：利率/匯率｜來源：Fed官方", global_lines)
        self.assertNotIn("Invalid official row", messages[3])
        self.assertTrue(any(call["year"] == 115 and call["month"] == "06" and call["co_id"] == "2301" for call in mops_calls))
        self.assertTrue(any(call["year"] == 115 and call["month"] == "07" and call["co_id"] == "2301" for call in mops_calls))

    def test_v20_4_47_future_watch_global_event_ranges_sort_and_fail_closed(self):
        payload = {
            "historical_analogy": {"line": "歷史類比：無高相似崩盤樣本｜依據不足/相似度低"},
            "mops_events": {"status": "available", "items": []},
            "global_events": collect_global_events(
                datetime(2026, 6, 4),
                global_event_source=[
                    {"date": "2026/06/15-16", "event": "日本央行 BOJ 利率會議", "impact": "利率/匯率", "source": "BOJ"},
                    {"date": "2026-06-16-17", "event": "Fed FOMC 利率決策/SEP", "impact": "利率/匯率", "source": "Fed"},
                    {"date": "2026/06/10-11", "event": "ECB 利率會議/記者會", "impact": "利率/匯率", "source": "ECB"},
                    {"date": "2026/06/10", "event": "美國 CPI（May 2026）", "impact": "通膨/利率", "source": "BLS"},
                    {"date": "2026/06/15-2026/06/17", "event": "G7 領袖峰會", "impact": "政治風險", "source": "G7"},
                    {"date": "2026/06/99-100", "event": "Invalid official row", "impact": "政治風險", "source": "Official"},
                    {"date": "bad-date", "event": "Bad date", "impact": "利率", "source": "Official"},
                ],
            ),
        }

        message = format_future_watch_message(payload, datetime(2026, 6, 4), generator.VERSION)
        global_lines = [
            line for line in message.splitlines()
            if "｜影響面：" in line and "來源：" in line
        ]

        self.assertEqual(global_lines[0], "06/10-11 ECB 利率會議/記者會｜影響面：利率/匯率｜來源：ECB官方")
        self.assertEqual(global_lines[1], "06/10 美國 CPI（May 2026）｜影響面：通膨/利率｜來源：BLS官方")
        self.assertEqual(global_lines[2], "06/15-16 日本央行 BOJ 利率會議｜影響面：利率/匯率｜來源：BOJ官方")
        self.assertIn("06/15-17 G7 領袖峰會｜影響面：政治風險｜來源：G7官方", global_lines)
        self.assertIn("06/16-17 Fed FOMC 利率決策/SEP｜影響面：利率/匯率｜來源：Fed官方", global_lines)
        self.assertNotIn("Invalid official row", message)
        self.assertNotIn("Bad date", message)

    def test_v20_4_47_live_twse_source_builds_pressure_timeline(self):
        responses = {
            "MI_INDEX": [
                {"指數": "發行量加權股價指數", "收盤指數": "45,677.46", "漲跌百分比": "-1.68"},
            ],
            "MI_5MINS_HIST": [
                {"Date": "1150601", "OpeningIndex": "44872.82", "HighestIndex": "45931.10", "LowestIndex": "44872.82", "ClosingIndex": "45337.91"},
                {"Date": "1150602", "OpeningIndex": "45388.93", "HighestIndex": "45915.92", "LowestIndex": "44869.38", "ClosingIndex": "45557.31"},
                {"Date": "1150603", "OpeningIndex": "45660.46", "HighestIndex": "46552.16", "LowestIndex": "45660.46", "ClosingIndex": "46459.16"},
                {"Date": "1150604", "OpeningIndex": "46364.07", "HighestIndex": "46364.07", "LowestIndex": "45677.46", "ClosingIndex": "45677.46"},
            ],
        }

        def fake_get_json(url, **_kwargs):
            key = "MI_INDEX" if "MI_INDEX" in url else "MI_5MINS_HIST"
            return SimpleNamespace(json=lambda: responses[key], raise_for_status=lambda: None)

        source = build_live_twse_historical_source(datetime(2026, 6, 4), get_json=fake_get_json)

        self.assertEqual(source["status"], "available")
        self.assertIn("2015/08/20-24 全球股災前段", source["line"])
        self.assertIn("差異：屬壓力前段，不是崩盤等級", source["line"])
        self.assertIn("source=TWSE", source["line"])
        self.assertEqual(source["today_features"]["change_pct"], -1.68)
        self.assertEqual(source["today_features"]["history_rows"], 4)

    def test_v20_4_47_live_mops_adapter_blocks_unparseable_spa_shell(self):
        def blocked_post(_url, **_kwargs):
            return SimpleNamespace(
                text="<script>location.href = location.origin + '/mops';</script>",
                raise_for_status=lambda: None,
            )

        result = live_mops_adapter({"co_id": "2301", "TYPEK": "sii", "year": 115, "month": "06"}, post_text=blocked_post)

        self.assertEqual(result["status"], "source-error")
        self.assertEqual(result["source"], "MOPS")

    def test_v20_4_47_live_mops_adapter_fails_closed_on_malformed_table(self):
        html = "<table><tr><th>日期</th><th>公司</th></tr><tr><td>-</td><td>2301 光寶科</td></tr></table>"

        def malformed_post(_url, **_kwargs):
            return SimpleNamespace(text=html, raise_for_status=lambda: None)

        result = live_mops_adapter({"co_id": "2301", "TYPEK": "sii", "year": 115, "month": "06"}, post_text=malformed_post)

        self.assertEqual(result["status"], "source-error")

        mops = collect_mops_events(
            {"光寶科": {"stock_code": "2301"}},
            datetime(2026, 6, 4),
            mops_adapter=lambda _params: result,
        )
        message = format_future_watch_message(
            {
                "historical_analogy": {"line": "歷史類比：無高相似崩盤樣本｜依據不足/相似度低｜source=TWSE"},
                "mops_events": mops,
                "global_events": {"status": "available", "items": []},
            },
            datetime(2026, 6, 4),
            generator.VERSION,
        )

        self.assertIn("未來30日法說會", message)
        self.assertIn("MOPS 官方來源暫時不可解析", message)

    def test_v20_4_47_live_mops_adapter_parses_future_official_table_rows(self):
        html = """
        <table><tr><th>日期</th><th>公司</th><th>內容</th></tr>
        <tr><td>115/06/20</td><td>2301 光寶科</td><td>召開法人說明會</td></tr></table>
        """

        def table_post(_url, **_kwargs):
            return SimpleNamespace(text=html, raise_for_status=lambda: None)

        result = live_mops_adapter({"co_id": "2301", "TYPEK": "sii", "year": 115, "month": "06"}, post_text=table_post)

        self.assertEqual(len(result["rows"]), 1)
        self.assertEqual(result["rows"][0]["co_id"], "2301")
        self.assertEqual(result["rows"][0]["event"], "法人說明會")

    def test_v20_4_47_mops_query_budget_limits_targets_and_calls(self):
        results = {
            f"股票{i}": {
                "stock_code": f"23{i:02d}",
                "holding": i < 2,
                "result": {"trade_state": "BUYABLE" if i == 2 else "OBSERVE"},
            }
            for i in range(12)
        }
        calls = []

        def adapter(params):
            calls.append(dict(params))
            return {"status": "available", "rows": []}

        mops = collect_mops_events(
            results,
            datetime(2026, 6, 4),
            mops_adapter=adapter,
            max_targets=2,
            max_queries=3,
        )

        self.assertEqual(mops["status"], "available")
        self.assertEqual(mops["target_count"], 2)
        self.assertEqual(mops["query_count"], 3)
        self.assertTrue(mops["budget_exhausted"])
        self.assertEqual(len(calls), 3)
        self.assertLessEqual(len({call["co_id"] for call in calls}), 2)

    def test_v20_4_47_mops_query_budget_checks_all_targets_first_market_before_fallback(self):
        results = {
            f"股票{i}": {
                "stock_code": f"23{i:02d}",
                "result": {"trade_state": "OBSERVE"},
            }
            for i in range(12)
        }
        calls = []

        def adapter(params):
            calls.append(dict(params))
            if params["co_id"] == "2311" and params["TYPEK"] == "sii" and params["month"] == "06":
                return {
                    "rows": [{
                        "date": "2026-06-20",
                        "co_id": "2311",
                        "name": "股票11",
                        "event": "法人說明會",
                    }]
                }
            return {"status": "available", "rows": []}

        mops = collect_mops_events(
            results,
            datetime(2026, 6, 4),
            mops_adapter=adapter,
            max_targets=12,
            max_queries=24,
        )

        self.assertEqual(mops["items"][0]["code"], "2311")
        self.assertEqual(calls[0]["TYPEK"], "sii")
        self.assertEqual(calls[-1]["co_id"], "2311")
        self.assertTrue(all(call["TYPEK"] == "sii" for call in calls))
        self.assertLessEqual(mops["query_count"], 24)

    def test_v20_4_47_mops_uses_exchange_typek_first_and_stops_after_rows(self):
        calls = []

        def adapter(params):
            calls.append(dict(params))
            if params["TYPEK"] == "otc":
                return {
                    "rows": [{
                        "date": "2026-06-20",
                        "co_id": "6488",
                        "name": "環球晶",
                        "event": "法人說明會",
                    }]
                }
            return {"status": "available", "rows": []}

        mops = collect_mops_events(
            {"環球晶": {"stock_code": "6488", "exchange": "上櫃"}},
            datetime(2026, 6, 4),
            mops_adapter=adapter,
            max_queries=8,
        )

        self.assertEqual(calls[0]["TYPEK"], "otc")
        self.assertEqual(mops["query_count"], 2)
        self.assertFalse(mops["budget_exhausted"])
        self.assertEqual(mops["items"][0]["code"], "6488")
        self.assertEqual(mops["items"][0]["reason"], "候選")

    def test_v20_4_47_live_global_events_parse_official_pages_or_seed_fallback(self):
        pages = {
            "federalreserve": "FOMC meeting calendar June 16-17",
            "bls.gov": "Consumer Price Index June 10, 2026",
            "boj.or.jp": "Monetary Policy Meeting June 15-16",
            "bea.gov": "GDP June 25, 2026",
            "ecb.europa": "Monetary policy meeting June 10-11",
        }

        def fake_get_text(url, **_kwargs):
            for key, body in pages.items():
                if key in url:
                    return SimpleNamespace(text=body, raise_for_status=lambda: None)
            raise AssertionError(url)

        source = build_live_global_event_source(datetime(2026, 6, 4), get_text=fake_get_text)
        events = collect_global_events(datetime(2026, 6, 4), source)
        lines = [item["date_label"] + " " + item["source"] for item in events["items"]]

        self.assertIn("06/10-11 ECB", lines)
        self.assertIn("06/10 BLS", lines)
        self.assertIn("06/15-16 BOJ", lines)
        self.assertIn("06/16-17 Fed", lines)
        self.assertIn("06/25 BEA", lines)

        def failing_get_text(_url, **_kwargs):
            raise TimeoutError("timeout")

        fallback = build_live_global_event_source(datetime(2026, 6, 4), get_text=failing_get_text)
        self.assertEqual(fallback["source"], "seed-fallback")
        self.assertGreaterEqual(len(fallback["events"]), 5)

    def test_v20_4_47_future_30d_watch_fails_closed_without_fake_events(self):
        holding_payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119],
            {"shares": 50, "avg_price": 118},
            price=119,
            change=1.4,
        )
        holding_payload["stock_code"] = "2301"

        def mops_adapter(_params):
            return {"status": "source-error"}

        messages = generator.formatTelegramMessages(
            {"光寶科": holding_payload},
            "FULL DETAIL",
            None,
            None,
            "⏳ 觀望",
            datetime(2026, 6, 15),
            report_phase="盤中",
            future_watch_sources={
                "historical_source": {
                    "samples": [{
                        "date": "2008-10-10",
                        "event": "金融海嘯急跌",
                        "similarity": 0.42,
                        "matched_features": ["跌幅擴大"],
                    }]
                },
                "mops_adapter": mops_adapter,
                "global_event_source": {"status": "source-error"},
            },
        )
        watch = future_watch_message(messages)

        self.assertEqual(len(messages), 4)
        self.assertIn("歷史類比：無高相似崩盤樣本｜依據不足/相似度低", watch)
        self.assertIn("未來30日法說會：MOPS 官方來源暫時不可解析，本次不列未確認事件", watch)
        self.assertIn("未來30日台股影響事件：官方來源暫時不可用，本次不列未確認事件", watch)
        self.assertNotIn("金融海嘯急跌", watch)
        self.assertNotIn("即將崩盤", watch)
        self.assertNotIn("重演", watch)
        self.assertNotIn("新倉建議", watch)

    def test_v20_4_47_generate_report_appends_live_readonly_future_watch_sources(self):
        holding_payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119],
            {"shares": 50, "avg_price": 118},
            price=119,
            change=1.4,
        )
        holding_payload["stock_code"] = "2301"
        watch_payload = render_payload(
            [50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69],
            None,
            price=69,
            change=1.2,
        )
        watch_payload["stock_code"] = "2421"

        def load_signal(name, _code):
            if name == "光寶科":
                return name, holding_payload, "BUY", None
            return name, watch_payload, "BUY", None

        def future_sources(now):
            return {
                "historical_source": {
                    "status": "insufficient-data",
                    "line": "歷史類比：2015/08/20-24 全球股災前段｜相似度 62%｜相似：單日跌幅 -1.68%、高檔回落 -1.88%、盤中震盪 +1.50%｜差異：屬壓力前段，不是崩盤等級｜關注：未來3-5日是否跌破本月低點｜source=TWSE",
                },
                "mops_adapter": lambda _params: {"status": "source-error"},
                "global_event_source": {
                    "status": "available",
                    "events": [
                        {"date": "2026/06/10-11", "event": "ECB 利率決策/記者會", "impact": "利率/匯率", "source": "ECB"},
                        {"date": "2026/06/10", "event": "美國 CPI（May 2026）", "impact": "通膨/利率", "source": "BLS"},
                        {"date": "2026/06/15-16", "event": "日本央行 BOJ 利率會議", "impact": "利率/匯率", "source": "BOJ"},
                        {"date": "2026/06/15-17", "event": "G7 領袖峰會", "impact": "政治風險", "source": "G7"},
                        {"date": "2026/06/16-17", "event": "Fed FOMC 利率決策/SEP", "impact": "利率/匯率", "source": "Fed"},
                        {"date": "2026/06/18", "event": "英國央行 BoE 利率決策", "impact": "利率/匯率", "source": "BoE"},
                    ],
                },
            }

        with patch.object(generator, "stocks", {"光寶科": "2301", "建準": "2421"}), \
             patch.object(generator, "load_positions", return_value={"光寶科": {"shares": 50, "avg_price": 118}}), \
             patch.object(generator, "load_today_position_events", return_value={}), \
             patch.object(generator, "get_position_store_warning", return_value=None), \
             patch.object(generator, "get_market_phase", return_value="盤中"), \
             patch.object(generator, "load_stock_signal", side_effect=load_signal), \
             patch.object(generator, "load_backtest_context", return_value={}), \
             patch.object(generator, "build_cross_day_contexts", return_value={}), \
             patch.object(generator, "default_future_watch_sources", side_effect=future_sources):
            messages, _reply_markup = generator.generate_report(dry_run=True)

        self.assertEqual(len(messages), 4)
        self.assertIn("【持倉標的】", messages[0])
        self.assertIn("【未持倉標的】", messages[1])
        self.assertIs(messages[2], summary_message(messages))
        watch = messages[3]
        self.assertIn(f"【06/04 未來30日關注｜{generator.VERSION}】", watch)
        self.assertIn("歷史類比：2015/08/20-24 全球股災前段", watch)
        self.assertIn("未來30日法說會：MOPS 官方來源暫時不可解析，本次不列未確認事件", watch)
        global_lines = [
            line for line in watch.splitlines()
            if "｜影響面：" in line and "來源：" in line
        ]
        self.assertEqual(len(global_lines), 5)
        self.assertEqual(global_lines[0], "06/10-11 ECB 利率決策/記者會｜影響面：利率/匯率｜來源：ECB官方")
        self.assertEqual(global_lines[1], "06/10 美國 CPI（May 2026）｜影響面：通膨/利率｜來源：BLS官方")
        self.assertIn("06/15-16 日本央行 BOJ 利率會議｜影響面：利率/匯率｜來源：BOJ官方", global_lines)
        self.assertIn("06/15-17 G7 領袖峰會｜影響面：政治風險｜來源：G7官方", global_lines)
        self.assertIn("06/16-17 Fed FOMC 利率決策/SEP｜影響面：利率/匯率｜來源：Fed官方", global_lines)
        self.assertNotIn("未來30日台股影響事件：官方來源暫時不可用", watch)
        self.assertNotIn("06/18 BoE MPC", watch)
        self.assertNotIn("06/25 BEA GDP", watch)
        first_three = "\n\n".join(messages[:3])
        self.assertIn("建準", first_three)
        self.assertNotIn("【未來30日關注】", first_three)
        self.assertNotIn("未來30日法說會", first_three)
        self.assertNotIn("未來30日台股影響事件", first_three)
        self.assertNotIn("即將崩盤", watch)
        self.assertNotIn("重演", watch)

    def test_position_cards_follow_summary_order_and_decision_wording(self):
        core_payload = render_payload(
            [40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 65],
            {"shares": 550, "avg_price": 52.15},
            price=65.4,
            change=9.9,
        )
        core_payload["stock_code"] = "2356"
        core_payload["result"]["price_behavior"] = "LIMIT_LOCK"
        core_payload["result"]["heat_state"] = "EXTREME"
        core_payload["result"]["extended_level"] = 3
        core_payload["holding_decision"] = {
            "action": "續抱核心倉",
            "level": "HOLD_CORE",
            "warning_price": 62.13,
            "hard_stop_price": 58.86,
        }

        bottom_payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119],
            {"shares": 200, "avg_price": 136.8},
            price=149,
            change=3.1,
        )
        bottom_payload["stock_code"] = "3231"
        bottom_payload["position_events"] = {"event_count": 1, "sold_shares": 430, "sell_pct": 98}
        bottom_payload["holding_decision"] = {
            "action": "續抱",
            "level": "HOLD",
            "warning_price": 141.55,
            "hard_stop_price": 139.54,
        }

        buy_payload = render_payload(
            [300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311, 312, 313, 314, 315, 316, 317, 318, 336],
            {"shares": 30, "avg_price": 334.5},
            price=336.5,
            change=4.3,
        )
        buy_payload["stock_code"] = "2376"
        buy_payload["position_events"] = {"event_count": 1, "bought_shares": 30}

        weak_payload = render_payload(
            [300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311, 312, 313, 314, 315, 316, 317, 318, 296],
            {"shares": 20, "avg_price": 298},
            price=296,
            change=-4.6,
        )
        weak_payload["stock_code"] = "2408"
        weak_payload["result"]["market_grade"] = "D"
        weak_payload["holding_decision"] = {
            "action": "續抱觀察",
            "level": "HOLD_WATCH",
            "note": "轉弱觀察，不加碼",
            "warning_price": 283.1,
            "hard_stop_price": 274.16,
        }

        messages = generator.formatTelegramMessages(
            {
                "技嘉": buy_payload,
                "南亞科": weak_payload,
                "緯創": bottom_payload,
                "英業達": core_payload,
            },
            "FULL DETAIL",
            None,
            None,
            "⏳ 觀望",
            datetime(2026, 5, 25),
        )

        position_msg = position_message(messages)
        self.assertLess(position_msg.index("【技嘉 2376】"), position_msg.index("【英業達 2356】"))
        self.assertLess(position_msg.index("【英業達 2356】"), position_msg.index("【緯創 3231】"))
        self.assertLess(position_msg.index("【技嘉 2376】"), position_msg.index("【南亞科 2408】"))
        self.assertIn("【技嘉 2376】📌 新倉風控觀察", position_msg)
        self.assertIn("【英業達 2356】📌 核心風控觀察", position_msg)
        self.assertIn("【緯創 3231】📌 減碼後觀察", position_msg)
        self.assertIn("【南亞科 2408】📌 續抱觀察", position_msg)
        self.assertIn("決策：新倉風控觀察，暫不加碼", position_msg)
        self.assertIn("決策：核心風控觀察，暫不加碼", position_msg)
        self.assertIn("決策：減碼後觀察，暫不加碼", position_msg)
        self.assertIn("條件：修復才恢復優先級，未修復續降級", position_msg)
        self.assertIn("決策：續抱觀察，轉弱觀察，不加碼", position_msg)

    def test_summary_with_holding_and_buy_has_no_zero_tracking_noise(self):
        holding_payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119],
            {"shares": 50, "avg_price": 118},
            price=119,
            change=1.4,
        )
        buy_payload = {
            "stock_code": "2421",
            "price": 120,
            "change": 1.2,
            "price_source": "realtime",
            "daily_source": "yahoo",
            "result": {
                "decision": "BUY",
                "action": 0.1,
                "action_type": "BUY",
                "rr": 2.0,
                "heat_state": "NORMAL",
                "trade_state": "WAIT",
                "structure_phase": "BREAKOUT_CONFIRM",
                "price_behavior": "NORMAL",
                "market_grade": "A",
                "volume_state": "STRONG",
                "volume_price_state": "EXPANSION",
                "structure_state": "STRONG",
                "entry_quality": "A",
                "confidence_score": 86,
                "breakout_distance": 0.5,
            },
            "holding": None,
            "structure_score": 5,
            "volume_ratio": 1.4,
        }

        messages = generator.formatTelegramMessages(
            {
                "智原": holding_payload,
                "建準": buy_payload,
            },
            "FULL DETAIL",
            "建準",
            9.2,
            "🟢 市場偏強",
            datetime(2026, 5, 26),
            strategy_evidence_summary=AVAILABLE_STRATEGY_EVIDENCE,
            report_phase="盤中",
        )

        self.assertIn("市場：中性觀察 R2｜執行動作 1（加碼10）｜新倉建議 1｜今日新建倉 0｜持倉風控 1｜未持倉 1（可買1/僅追蹤0/淘汰0）", summary_message(messages))
        self.assertIn("智原 加碼10（加碼後守警戒價，量價未延續則停止加碼）", summary_message(messages))
        self.assertIn("建準 可買（分批，不追價）", summary_message(messages))
        self.assertIn("未持倉 1｜可買 1｜不可追高觀察 0（不可買）｜淘汰 0", summary_message(messages))
        self.assertNotIn("其中僅追蹤 0 檔拆分", summary_message(messages))
        self.assertIn("📎 詳情索引：持倉 智原｜交易執行 1｜新倉建議 1", summary_message(messages))
        self.assertNotIn("未持倉 0 檔僅追蹤", summary_message(messages))
        self.assertNotIn("其餘 0 檔僅追蹤", summary_message(messages))

    def test_v20_4_25_holding_card_hides_precise_execution_when_ledger_insufficient(self):
        holding_payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119],
            {"shares": 70, "avg_price": 118},
            price=119,
            change=1.4,
        )
        holding_payload["stock_code"] = "3035"
        holding_payload["position_events"] = {"event_count": 1, "bought_shares": 70}
        holding_payload["cross_day_context"] = {
            "source_status": "insufficient-data",
            "source_of_truth": ["position_events"],
            "execution_memory": {},
        }

        messages = generator.formatTelegramMessages(
            {"智原": holding_payload},
            "FULL DETAIL",
            None,
            None,
            "⏳ 觀望",
            datetime(2026, 5, 26),
            strategy_evidence_summary=AVAILABLE_STRATEGY_EVIDENCE,
            report_phase="盤中",
        )
        card = card_block(position_message(messages), "【智原 3035】")
        evidence = evidence_message(messages)

        self.assertIn("今日執行：執行記憶不足，暫不顯示精確執行欄位", card)
        self.assertNotIn("倉位：70股", card)
        self.assertNotIn("均價", card)
        self.assertNotIn("今日 買", card)
        self.assertNotIn("資料依據", evidence)

    def test_unheld_funnel_prepare_count_has_separate_tracking_parent(self):
        states = {
            "準備股": "可準備",
            "冷卻一": "等冷卻",
            "冷卻二": "等冷卻",
            "RR股": "等RR修復",
        }

        with patch.object(generator, "unheld_funnel_state", side_effect=lambda name, _data, **_kwargs: states[name]):
            text = generator.format_unheld_funnel([(name, {}) for name in states])

        self.assertIn("未持倉 4｜可買 0｜不可追高觀察 1（不可買）｜僅追蹤 3（等冷卻2/等RR修復1）｜淘汰 0", text)
        self.assertNotIn("未持倉總數 4 檔", text)
        self.assertNotIn("其中僅追蹤 3 檔拆分", text)
        self.assertNotIn("非執行準備/追蹤合計", text)
        self.assertNotIn("非執行追蹤 4 檔，僅追蹤不可買", text)
        self.assertNotIn("其中：等冷卻 2、等回測 0、等RR修復 1、等量能 0", text)

    def test_unheld_funnel_counts_next_day_confirmation_separately_from_cooling(self):
        states = {
            "隔日股": "隔日確認",
        }

        with patch.object(generator, "unheld_funnel_state", side_effect=lambda name, _data, **_kwargs: states[name]):
            text = generator.format_unheld_funnel([(name, {}) for name in states])

        self.assertIn("未持倉 1｜可買 0｜不可追高觀察 0（不可買）｜隔日確認 1｜僅追蹤 1｜淘汰 0", text)
        self.assertIn("可買 0｜不可追高觀察 0（不可買）｜隔日確認 1｜僅追蹤 1｜淘汰 0", text)
        self.assertNotIn("未持倉總數 1 檔", text)
        self.assertNotIn("其中僅追蹤 1 檔拆分", text)
        self.assertNotIn("非執行準備/追蹤合計", text)
        self.assertNotIn("等冷卻 1", text)

    def test_unheld_next_day_confirmation_card_and_funnel_counts_match(self):
        payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 124],
            None,
            price=124,
            change=3.2,
        )
        payload["stock_code"] = "3035"
        payload["result"].update({
            "decision": "WAIT",
            "action": 0,
            "price_behavior": "LIMIT_REBOUND",
            "heat_state": "NORMAL",
            "trade_state": "WAIT",
            "rr": 1.5,
            "market_grade": "A",
            "entry_quality": "B",
        })

        messages = generator.formatTelegramMessages(
            {"智原": payload},
            "FULL DETAIL",
            None,
            None,
            {"market_theme_evidence": {"theme_status": "absent", "level": "absent"}},
            datetime(2026, 6, 2),
            report_phase="盤中",
        )

        summary = summary_message(messages)
        unheld = unheld_message(messages)

        self.assertIn("可買 0｜不可追高觀察 0（不可買）｜隔日確認 1｜僅追蹤 1｜淘汰 0", summary)
        self.assertNotIn("其中僅追蹤 1 檔拆分", summary)
        self.assertNotIn("非執行準備/追蹤合計", summary)
        self.assertIn("【智原 3035】👀 隔日確認｜漲停反彈待確認", unheld)
        self.assertNotIn("等冷卻 1", summary)

    def test_unheld_cooling_and_next_day_rendered_counts_match_cards(self):
        next_day_payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 124],
            None,
            price=124,
            change=3.2,
        )
        next_day_payload["stock_code"] = "3035"
        next_day_payload["result"].update({
            "decision": "WAIT",
            "action": 0,
            "price_behavior": "LIMIT_REBOUND",
            "heat_state": "NORMAL",
            "trade_state": "WAIT",
            "rr": 1.5,
            "market_grade": "A",
            "entry_quality": "B",
        })
        cooling_payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 125],
            None,
            price=125,
            change=4.0,
        )
        cooling_payload["stock_code"] = "2301"
        cooling_payload["result"].update({
            "decision": "WAIT",
            "action": 0,
            "price_behavior": "NORMAL",
            "heat_state": "HOT",
            "trade_state": "EXTENDED",
            "rr": 1.6,
            "market_grade": "A",
            "entry_quality": "B",
        })

        messages = generator.formatTelegramMessages(
            {"智原": next_day_payload, "光寶科": cooling_payload},
            "FULL DETAIL",
            None,
            None,
            {"market_theme_evidence": {"theme_status": "absent", "level": "absent"}},
            datetime(2026, 6, 2),
            report_phase="盤中",
        )

        summary = summary_message(messages)
        unheld = unheld_message(messages)

        self.assertIn("未持倉 2｜可買 0｜不可追高觀察 0（不可買）｜隔日確認 1｜僅追蹤 2（等冷卻）｜淘汰 0", summary)
        self.assertIn("【智原 3035】👀 隔日確認｜漲停反彈待確認", unheld)
        self.assertIn("【光寶科 2301】⏳ 等冷卻｜過熱觀察", unheld)
        self.assertEqual(summary.count("隔日確認 1"), 1)
        self.assertNotIn("【智原 3035】⏳ 等冷卻", unheld)
        self.assertNotIn("【光寶科 2301】👀 隔日確認", unheld)

    def test_summary_includes_strategy_evidence_without_changing_actions(self):
        payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119],
            None,
            price=119,
            change=1.4,
        )
        payload["stock_code"] = "2421"
        payload["result"]["decision"] = "BUY"
        payload["result"]["action"] = 0.1

        messages = generator.formatTelegramMessages(
            {"建準": payload},
            "FULL DETAIL",
            "建準",
            9.2,
            "🟢 市場偏強",
            datetime(2026, 5, 26),
            strategy_evidence_summary=structured_strategy_evidence(
                "insufficient-data",
                row_count=3,
                rendered_text=(
                    "📊 策略證據 v20.0\n"
                    "策略樣本 / 分類回測\n"
                    "狀態：不可用\n"
                    "原因：classification backtest 樣本不足（有效樣本 3）\n"
                    "解讀：本次不把策略樣本納入判斷；個股決策只看既有買點與風控。\n"
                    "狀態碼：insufficient-sample"
                ),
            ),
        )

        summary = summary_message(messages)
        evidence = evidence_message(messages)
        context = generator.build_report_context(
            {"建準": payload},
            "🟢 市場偏強",
            datetime(2026, 5, 26),
            strategy_evidence_summary=structured_strategy_evidence(
                "insufficient-data",
                row_count=3,
                rendered_text=(
                    "📊 策略證據 v20.0\n"
                    "策略樣本 / 分類回測\n"
                    "狀態：不可用\n"
                    "原因：classification backtest 樣本不足（有效樣本 3）\n"
                    "解讀：本次不把策略樣本納入判斷；個股決策只看既有買點與風控。\n"
                    "狀態碼：insufficient-sample"
                ),
            ),
        )
        self.assertNotIn("📊 策略證據 v20.0", summary)
        self.assertNotIn("策略樣本 / 分類回測", summary)
        self.assertIn("v20.4.47 簡報", evidence)
        self.assertNotIn("資料依據", evidence)
        self.assertEqual(context["source_status"]["strategy_sample"], "insufficient-data")
        self.assertTrue(context["evidence_status"]["strategy_sample"])
        self.assertEqual(payload["result"]["decision"], "BUY")
        self.assertEqual(payload["result"]["action"], 0.1)

    def test_unheld_cards_follow_summary_group_order(self):
        limit_payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 125],
            None,
            price=125,
            change=9.6,
        )
        limit_payload["stock_code"] = "2303"
        limit_payload["result"]["price_behavior"] = "LIMIT_LOCK"

        wait_payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119],
            None,
            price=119,
            change=1.4,
        )
        wait_payload["stock_code"] = "2421"
        wait_payload["result"]["rr"] = 0.5

        hot_payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 123],
            None,
            price=123,
            change=4.2,
        )
        hot_payload["stock_code"] = "2301"
        hot_payload["result"]["heat_state"] = "HOT"
        hot_payload["result"]["trade_state"] = "EXTENDED"
        hot_payload["result"]["rr"] = 0.78

        weak_payload = render_payload(
            [100, 99, 98, 97, 96, 95, 94, 93, 92, 91, 90, 89, 88, 87, 86, 85, 84, 83, 82, 81],
            None,
            price=81,
            change=-2.0,
        )
        weak_payload["stock_code"] = "2337"
        weak_payload["result"]["market_grade"] = "D"

        messages = generator.formatTelegramMessages(
            {
                "旺宏": weak_payload,
                "建準": wait_payload,
                "光寶科": hot_payload,
                "聯電": limit_payload,
            },
            "FULL DETAIL",
            None,
            None,
            "⏳ 觀望",
            datetime(2026, 5, 25),
            report_phase="盤中",
        )

        summary_msg = summary_message(messages)
        unheld_msg = unheld_message(messages)
        self.assertIn("未持倉漏斗（非執行）：", summary_msg)
        self.assertIn("未持倉 4｜可買 0｜不可追高觀察 1（不可買）｜僅追蹤 2（等冷卻1/等RR修復1）｜淘汰 1", summary_msg)
        self.assertIn("未持倉 1 檔不可追高觀察、2 檔僅追蹤，等觸發，不列入今日盤中交易執行", summary_msg)
        self.assertIn("強勢準備：\n- 漲停鎖價：聯電 不可追高，待開板回測", summary_msg)
        self.assertIn("淘汰 1 檔｜主因：市場弱｜詳情見未持倉卡", summary_msg)
        self.assertLess(unheld_msg.index("【聯電 2303】"), unheld_msg.index("【光寶科 2301】"))
        self.assertLess(unheld_msg.index("【光寶科 2301】"), unheld_msg.index("【建準 2421】"))
        self.assertLess(unheld_msg.index("【建準 2421】"), unheld_msg.index("【旺宏 2337】"))
        self.assertIn("【聯電 2303】👀 不可追高觀察｜漲停鎖價", unheld_msg)
        self.assertIn("【光寶科 2301】⏳ 等冷卻｜過熱觀察", unheld_msg)
        self.assertIn("【建準 2421】👀 等RR修復", unheld_msg)
        self.assertIn("【旺宏 2337】⛔ 淘汰", unheld_msg)

    def test_unheld_far_from_trigger_tracks_retest_instead_of_rejecting(self):
        payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 126],
            None,
            price=126,
            change=2.0,
        )
        payload["stock_code"] = "2303"
        payload["result"].update({
            "decision": "WAIT",
            "price_behavior": "NORMAL",
            "heat_state": "NORMAL",
            "trade_state": "WAIT",
            "structure_phase": "BREAKOUT",
            "market_grade": "A",
            "entry_quality": "B",
            "rr": 1.4,
            "breakout_distance": 7,
        })

        messages = generator.formatTelegramMessages(
            {"聯電": payload},
            "FULL DETAIL",
            None,
            None,
            "⏳ 觀望",
            datetime(2026, 5, 27),
            report_phase="盤中",
        )

        self.assertEqual(generator.unheld_funnel_state("聯電", payload), "等回測")
        self.assertIn("未持倉 1｜可買 0｜不可追高觀察 0（不可買）｜僅追蹤 1（等回測）｜淘汰 0", summary_message(messages))
        self.assertIn("僅追蹤 1（等回測）", summary_message(messages))
        self.assertIn("【聯電 2303】⏳ 等回測｜遠離觸發", unheld_message(messages))

    def test_rejected_weak_rr_uses_true_reject_reason_not_rr(self):
        payload = render_payload(
            [120, 118, 116, 114, 112, 110, 108, 106, 104, 102, 100, 98, 96, 94, 92, 90, 88, 86, 84, 85],
            None,
            price=85,
            change=1.2,
        )
        payload["stock_code"] = "2337"
        payload["result"].update({
            "decision": "WAIT",
            "price_behavior": "NORMAL",
            "structure_phase": "WEAK",
            "market_grade": "D",
            "rr": 0.4,
            "breakout_distance": 9,
        })

        messages = generator.formatTelegramMessages(
            {"旺宏": payload},
            "FULL DETAIL",
            None,
            None,
            "⏳ 觀望",
            datetime(2026, 5, 27),
            report_phase="盤中",
        )

        self.assertEqual(generator.unheld_funnel_state("旺宏", payload), "淘汰")
        self.assertIn("淘汰 1 檔｜主因：市場弱｜詳情見未持倉卡", summary_message(messages))
        self.assertIn("【旺宏 2337】⛔ 淘汰｜市場弱", unheld_message(messages))
        self.assertIn("買點：不可買，等市場轉強", unheld_message(messages))
        self.assertIn("盤中觸發：重新轉強前不列優先", unheld_message(messages))
        self.assertNotIn("淘汰 1 檔｜主因：RR不足", summary_message(messages))
        self.assertNotIn("【旺宏 2337】⛔ 淘汰｜RR不足", unheld_message(messages))
        self.assertNotIn("等RR達標", unheld_message(messages))

    def test_unheld_price_line_keeps_closing_parenthesis(self):
        payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 128.5],
            None,
            price=128.5,
            change=2.8,
        )
        payload["stock_code"] = "2344"

        card = generator.formatTelegramUnheldCard("華邦電", payload)

        self.assertIn("價格：128.5（+2.80%）", card)
        self.assertNotIn("價格：128.5（+2.80%\n", card)

    def test_daily_write_warning_is_in_default_summary_message(self):
        payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119],
            None,
            price=119,
            change=1.4,
        )
        payload["stock_code"] = "2344"
        warning = generator.daily_write_warning_text(
            {"recorded": False, "missing_stock_ids": ["2421"]},
            {"recorded": False, "missing_stock_ids": ["3035"]}
        )

        messages = generator.formatTelegramMessages(
            {"華邦電": payload},
            "FULL DETAIL",
            None,
            None,
            "⏳ 觀望",
            datetime(2026, 5, 25),
            daily_write_warning=warning,
        )

        self.assertEqual(len(messages), 3)
        self.assertIn("每日快照未寫入", summary_message(messages))
        self.assertIn("缺少 3035, 2421", summary_message(messages))
        self.assertNotIn("每日快照未寫入", position_message(messages))
        self.assertNotIn("每日快照未寫入", unheld_message(messages))

    def test_decision_brief_keeps_legal_production_summary_line(self):
        header = f"【05/25 盤中｜{generator.VERSION}】"
        source_line = "Source：production runtime metadata"
        legal_summary_line = "🧭 今日結論：production 資料來源正常，今日仍無有效進場"
        brief = generator.format_brief_data_evidence_message(
            {
                "report_context": {
                    "report_phase": "盤中",
                    "as_of_date": "2026-05-25",
                    "trade_date": "2026-05-25",
                },
                "source_status_summary": {},
                "evidence_manifest": [],
                "market_theme_evidence": {"confirmed": False, "source_status": "missing-source"},
            },
            [],
            [],
            summary_message="\n".join([header, source_line, legal_summary_line]),
            summary_excluded_lines={header, source_line},
        )

        self.assertIn(legal_summary_line, brief)
        self.assertNotIn(source_line, brief)

    def test_afterhours_brief_uses_structured_daily_write_warning(self):
        payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119],
            None,
            price=119,
            change=1.4,
        )
        payload["stock_code"] = "2344"
        warning = "每日快照未寫入：請檢查寫入來源"

        messages = generator.formatTelegramMessages(
            {"華邦電": payload},
            "FULL DETAIL",
            None,
            None,
            "⏳ 觀望",
            datetime(2026, 5, 25),
            daily_write_warning=warning,
            report_phase="盤後",
        )

        self.assertIn(f"資料寫入：{warning}，明日前確認補寫狀態。", summary_message(messages))
        self.assertNotIn("每日快照未寫入", position_message(messages))
        self.assertNotIn("每日快照未寫入", unheld_message(messages))

    def test_v19_3_2_intraday_summary_classifies_0526_cases(self):
        def payload(code, price, change, result, holding=None, decision=None):
            return {
                "stock_code": code,
                "price": price,
                "change": change,
                "price_source": "realtime",
                "daily_source": "yahoo",
                "result": {
                    "decision": "WAIT",
                    "action": 0,
                    "rr": 0,
                    "heat_state": "NORMAL",
                    "trade_state": "WAIT",
                    "structure_phase": "BASE",
                    "price_behavior": "NORMAL",
                    "market_grade": "B",
                    "volume_state": "NORMAL",
                    "volume_price_state": "NORMAL",
                    "structure_state": "NORMAL",
                    "entry_quality": "D",
                    "confidence_score": 49,
                    "breakout_distance": 0,
                    **result,
                },
                "holding": holding,
                "holding_decision": decision,
                "structure_score": 3,
                "volume_ratio": 1,
            }

        results = {
            "英業達": payload("2356", 62.25, -4.82, {"heat_state": "HOT", "trade_state": "EXTENDED"}, {"shares": 550, "avg_price": 52.15}, {"action": "核心續抱", "level": "HOLD_CORE", "note": "高浮盈回落，暫不加碼", "warning_price": 59.14, "hard_stop_price": 54.76}),
            "緯創": payload("3231", 146.75, -1.51, {"structure_phase": "SHAKEOUT", "volume_state": "WEAK"}, {"shares": 200, "avg_price": 136.8}, {"action": "洗盤續抱", "level": "SHAKEOUT", "note": "縮量回測，未見出貨", "warning_price": 139.41, "hard_stop_price": 125.86}),
            "南亞科": payload("2408", 308.75, 4.31, {"structure_phase": "WEAK", "volume_state": "WEAK", "breakout_distance": 11}, {"shares": 30, "avg_price": 298}, {"action": "續抱觀察", "level": "HOLD_WATCH", "note": "轉弱觀察，不加碼", "warning_price": 293.31, "hard_stop_price": 274.16}),
            "技嘉": payload("2376", 336.25, -0.07, {"structure_phase": "SHAKEOUT", "volume_state": "WEAK"}, {"shares": 30, "avg_price": 334.5}, {"action": "洗盤續抱", "level": "SHAKEOUT", "note": "縮量回測，未見出貨", "warning_price": 317.77, "hard_stop_price": 307.74}),
            "智原": payload("3035", 210.25, -3.78, {"structure_phase": "SHAKEOUT", "volume_state": "WEAK"}, {"shares": 40, "avg_price": 211.5}, {"action": "洗盤警戒", "level": "SHAKEOUT_WARN", "note": "小虧，暫不加碼", "warning_price": 200.92, "hard_stop_price": 194.58}),
            "華邦電": payload("2344", 141, 9.73, {"price_behavior": "LIMIT_LOCK", "structure_phase": "LOCK_LIMIT", "heat_state": "EXTREME", "trade_state": "AVOID", "rr": 0.23}),
            "聯電": payload("2303", 130.75, 4.6, {"heat_state": "EXTREME", "trade_state": "AVOID", "rr": 0}),
            "群創": payload("3481", 46.225, -5.86, {"heat_state": "EXTREME", "trade_state": "AVOID", "rr": 0}),
            "光寶科": payload("2301", 237.25, 4.29, {"heat_state": "HOT", "trade_state": "EXTENDED", "rr": 0.78}),
            "建準": payload("2421", 163.25, 0.46, {"trade_state": "LATE_ENTRY", "rr": 0.12, "volume_state": "WEAK", "market_grade": "A"}),
            "仁寶": payload("2324", 33.325, -3.82, {"trade_state": "LATE_ENTRY", "rr": 0.26, "market_grade": "A"}),
            "旺宏": payload("2337", 159.25, 4.43, {"structure_phase": "WEAK_REBOUND", "price_behavior": "WEAK_REBOUND", "market_grade": "D", "volume_state": "WEAK", "rr": 2.44, "breakout_distance": 8.55}),
        }

        with patch.object(generator, "get_market_phase", return_value="盤中"):
            messages = generator.formatTelegramMessages(
                results,
                "FULL DETAIL",
                None,
                None,
                "🚨 過熱控倉，先處理持倉",
                datetime(2026, 5, 26),
            )

        self.assertIn("v20.4.47", summary_message(messages))
        self.assertIn("📡 資料：即時價 realtime｜日線 yahoo", summary_message(messages))
        self.assertIn("市場：進攻偏熱 R3｜執行動作 0｜今日新建倉 0｜持倉風控 5｜未持倉 7（僅追蹤6/淘汰1）", summary_message(messages))
        self.assertNotIn("市場/結論：進攻偏熱｜R3；R3 進攻偏熱", summary_message(messages))
        self.assertIn("原因：持倉多數依風控處理，新倉無有效進場。", summary_message(messages))
        self.assertIn("風險：持倉：hard_stop 永不豁免", summary_message(messages))
        self.assertNotIn("✅ 今日盤中交易執行", summary_message(messages))
        self.assertNotIn("無新增下單", summary_message(messages))
        self.assertIn("持倉風控檢查", summary_message(messages))
        self.assertIn("1. 英業達｜+19.37%｜核心風控觀察｜守警戒價", summary_message(messages))
        self.assertIn("2. 緯創｜+7.27%｜洗盤續抱｜跌破警戒升級風控", summary_message(messages))
        self.assertIn("5. 智原｜-0.59%｜洗盤警戒｜跌破警戒升級風控", summary_message(messages))
        self.assertIn("未持倉 6 檔僅追蹤，等觸發，不列入今日盤中交易執行", summary_message(messages))
        self.assertIn("未持倉漏斗（非執行）：", summary_message(messages))
        self.assertIn("未持倉 7｜可買 0｜不可追高觀察 0（不可買）｜僅追蹤 6（等冷卻3/等回測1/等RR修復2）｜淘汰 1", summary_message(messages))
        self.assertNotIn("僅追蹤 6 檔，不列入交易執行", summary_message(messages))
        self.assertIn("📎 詳情索引：持倉 英業達、緯創、南亞科、技嘉、智原｜僅追蹤 6｜淘汰 1", summary_message(messages))
        self.assertIn("淘汰 1 檔｜主因：弱反彈待確認｜詳情見未持倉卡", summary_message(messages))
        self.assertIn("【光寶科 2301】⏳ 等冷卻｜過熱觀察", unheld_message(messages))
        self.assertIn("【建準 2421】👀 等RR修復｜RR不足", unheld_message(messages))
        self.assertIn("【旺宏 2337】⛔ 淘汰｜弱反彈待確認", unheld_message(messages))
        self.assertIn("數據：不適用（既有持倉）", position_message(messages))
        self.assertIn("RR -（過熱）", unheld_message(messages))
        self.assertIn("RR：-（不可行動）", unheld_message(messages))

    def test_v19_3_4_backtest_line_explains_confidence_and_verdict(self):
        self.assertEqual(
            generator.compact_backtest_line({
                "sample": 35,
                "win_rate": 46,
                "avg_return": -0.6,
            }),
            "回測：樣本35｜參考度高｜3日勝率46%｜相對-0.6%｜偏弱",
        )
        self.assertEqual(
            generator.compact_backtest_line({
                "sample": 8,
                "win_rate": 50,
                "avg_return": 0.3,
            }),
            "回測：不可用｜樣本不足（有效樣本8）｜不納入判斷",
        )
        self.assertEqual(
            generator.compact_backtest_line({
                "sample": 15,
                "win_rate": 60,
                "avg_return": 1.8,
            }),
            "回測：樣本15｜參考度中｜3日勝率60%｜相對+1.8%｜略優",
        )
        self.assertEqual(generator.compact_backtest_line(None), "回測：-")

    def test_v19_3_4_new_position_loss_displays_risk_watch_and_next_step(self):
        payload = {
            "stock_code": "2376",
            "price": 99,
            "change": -1.0,
            "price_source": "realtime",
            "daily_source": "yahoo",
            "result": {
                "decision": "WAIT",
                "action": 0,
                "rr": 1.2,
                "heat_state": "NORMAL",
                "trade_state": "WAIT",
                "structure_phase": "BASE",
                "price_behavior": "NORMAL",
                "market_grade": "B",
                "volume_state": "NORMAL",
                "volume_price_state": "NORMAL",
                "structure_state": "NORMAL",
                "entry_quality": "D",
                "confidence_score": 49,
                "breakout_distance": 0,
            },
            "holding": {"shares": 30, "avg_price": 100},
            "holding_decision": {
                "action": "續抱",
                "level": "HOLD_WATCH",
                "note": "不加碼",
                "warning_price": 95,
                "hard_stop_price": 90,
            },
            "position_events": {"event_count": 1, "bought_shares": 30},
            "structure_score": 3,
            "volume_ratio": 1.0,
        }

        card = generator.formatTelegramPositionCard("技嘉", payload)

        self.assertIn("【技嘉 2376】📌 新倉風控觀察｜-1.00%", card)
        self.assertIn("決策：新倉風控觀察，暫不加碼", card)
        self.assertIn("條件：守警戒價，跌破停損或轉弱優先風控", card)
        self.assertIn("下一步：盤中先觀察，未修復再降級", card)
        self.assertNotIn("明日未修復", card)
        self.assertNotIn("隔日未修復", card)

    def test_light_loss_shakeout_holding_displays_warning_even_when_decision_is_watch(self):
        payload = {
            "stock_code": "3035",
            "price": 209.75,
            "change": -0.8,
            "price_source": "realtime",
            "daily_source": "yahoo",
            "result": {
                "decision": "WAIT",
                "action": 0,
                "rr": 1.2,
                "heat_state": "NORMAL",
                "trade_state": "WAIT",
                "structure_phase": "SHAKEOUT",
                "price_behavior": "NORMAL",
                "market_grade": "B",
                "volume_state": "WEAK",
                "volume_price_state": "COILING",
                "structure_state": "NORMAL",
                "entry_quality": "D",
                "confidence_score": 49,
                "breakout_distance": 0,
            },
            "holding": {"shares": 40, "avg_price": 211.5},
            "holding_decision": {
                "action": "續抱",
                "level": "HOLD_WATCH",
                "note": "不加碼",
                "warning_price": 200.92,
                "hard_stop_price": 194.58,
            },
            "structure_score": 3,
            "volume_ratio": 0.7,
        }

        card = generator.formatTelegramPositionCard("智原", payload)

        self.assertIn("【智原 3035】📌 洗盤警戒｜-0.83%", card)
        self.assertIn("決策：洗盤警戒，暫不加碼", card)
        self.assertIn("條件：若跌破停損或轉弱，優先風控", card)

    def test_rr_zero_display_marks_insufficient_when_not_hidden(self):
        self.assertEqual(
            generator.rr_display_text({
                "rr": 0,
                "heat_state": "NORMAL",
                "trade_state": "WAIT",
                "market_grade": "B",
                "structure_phase": "BASE",
                "volume_state": "NORMAL",
                "breakout_distance": 0,
            }),
            "0.00（不足）"
        )

    def test_unheld_overheat_prepare_rr_value_uses_overheat_blocker(self):
        payload = {
            "stock_code": "2376",
            "price": 336.25,
            "change": -0.07,
            "price_source": "realtime",
            "daily_source": "yahoo",
            "result": {
                "decision": "WAIT",
                "action": 0,
                "rr": 0.21,
                "calc_rr": 0.21,
                "heat_state": "HOT",
                "trade_state": "EXTENDED",
                "structure_phase": "BREAKOUT_CONFIRM",
                "price_behavior": "NORMAL",
                "market_grade": "A",
                "volume_state": "NORMAL",
                "volume_price_state": "NORMAL",
                "structure_state": "STRONG",
                "entry_quality": "A",
                "confidence_score": 72,
                "breakout_distance": 0,
            },
            "holding": None,
            "structure_score": 4,
            "volume_ratio": 1.2,
        }

        card = generator.formatTelegramUnheldCard("技嘉", payload, market_mode="進攻偏熱")

        self.assertIn("【技嘉 2376】⏳ 等冷卻｜過熱觀察", card)
        self.assertIn("買點：不買，等冷卻", card)
        self.assertIn("數據：RR -（過熱）", card)
        self.assertNotIn("RR 0.21", card)

    def test_unheld_previous_eliminated_single_valid_entry_stays_conservative(self):
        payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119],
            None,
            price=119,
            change=1.0,
        )
        payload["stock_code"] = "2301"
        payload["result"].update({
            "decision": "BUY",
            "action": 0.1,
            "rr": 1.6,
            "breakout_distance": 0.5,
            "heat_state": "NORMAL",
            "trade_state": "READY",
            "market_grade": "A",
            "entry_quality": "A",
        })
        payload["cross_day_context"] = {
            "source_status": "ready",
            "source_of_truth": ["daily_signal_snapshot"],
            "previous_state": "eliminated",
            "consecutive_buy_signals": 1,
        }

        self.assertEqual(generator.unheld_funnel_state("光寶科", payload), "淘汰")
        self.assertIn("單次買點不直接翻可買", payload["evidence_adjustment_reason"])
        card = generator.formatTelegramUnheldCard("光寶科", payload, report_phase="盤中")
        self.assertNotIn("可買｜", card)
        self.assertNotIn("不買｜進場", card)
        self.assertIn("【光寶科 2301】⛔ 不買｜前態待確認", card)
        self.assertIn("淘汰", card)

        payload["cross_day_context"]["consecutive_buy_signals"] = 2
        self.assertEqual(generator.unheld_funnel_state("光寶科", payload), "可買")

    def test_v19_3_3_valid_buy_is_summary_buy_group_not_watch_group(self):
        payload = {
            "stock_code": "2421",
            "price": 120,
            "change": 1.2,
            "price_source": "realtime",
            "daily_source": "yahoo",
            "result": {
                "decision": "BUY",
                "action": 0.1,
                "action_type": "BUY",
                "rr": 2.0,
                "heat_state": "NORMAL",
                "trade_state": "WAIT",
                "structure_phase": "BREAKOUT_CONFIRM",
                "price_behavior": "NORMAL",
                "market_grade": "A",
                "volume_state": "STRONG",
                "volume_price_state": "EXPANSION",
                "structure_state": "STRONG",
                "entry_quality": "A",
                "confidence_score": 86,
                "breakout_distance": 0.5,
            },
            "holding": None,
            "structure_score": 5,
            "volume_ratio": 1.4,
        }

        messages = generator.formatTelegramMessages(
            {"建準": payload},
            "FULL DETAIL",
            "建準",
            9.2,
            "🟢 市場偏強",
            datetime(2026, 5, 26),
            strategy_evidence_summary=AVAILABLE_STRATEGY_EVIDENCE,
            report_phase="盤中",
        )

        self.assertIn("建準 可買（分批，不追價）", summary_message(messages))
        self.assertIn("未持倉 1｜可買 1｜不可追高觀察 0（不可買）｜淘汰 0", summary_message(messages))
        self.assertNotIn("其中僅追蹤 0 檔拆分", summary_message(messages))
        self.assertNotIn("建準｜等", summary_message(messages))
        self.assertIn("【建準 2421】🟢 可買｜10%倉｜買點成立", unheld_message(messages))
        self.assertIn("買點：可買｜建議 10%倉｜現在可分批", unheld_message(messages))

    def test_v19_4_tracking_states_do_not_override_valid_buy_or_weak_reject(self):
        buy_payload = {
            "stock_code": "2421",
            "price": 120,
            "change": 1.2,
            "price_source": "realtime",
            "daily_source": "yahoo",
            "result": {
                "decision": "BUY",
                "action": 0.1,
                "action_type": "BUY",
                "rr": 2.0,
                "heat_state": "NORMAL",
                "trade_state": "WAIT",
                "structure_phase": "BREAKOUT_CONFIRM",
                "price_behavior": "NORMAL",
                "market_grade": "A",
                "volume_state": "STRONG",
                "volume_price_state": "EXPANSION",
                "structure_state": "STRONG",
                "entry_quality": "A",
                "confidence_score": 86,
                "breakout_distance": 0.5,
            },
            "holding": None,
            "structure_score": 5,
            "volume_ratio": 1.4,
        }
        weak_payload = dict(buy_payload)
        weak_payload["stock_code"] = "2337"
        weak_payload["result"] = {
            **buy_payload["result"],
            "decision": "WAIT",
            "action": 0,
            "rr": 2.0,
            "market_grade": "D",
            "structure_phase": "WEAK_REBOUND",
            "price_behavior": "WEAK_REBOUND",
        }

        messages = generator.formatTelegramMessages(
            {"建準": buy_payload, "旺宏": weak_payload},
            "FULL DETAIL",
            "建準",
            9.2,
            "🟢 市場偏強",
            datetime(2026, 5, 26),
            strategy_evidence_summary=AVAILABLE_STRATEGY_EVIDENCE,
            report_phase="盤中",
        )

        self.assertIn("建準 可買（分批，不追價）", summary_message(messages))
        self.assertIn("未持倉 2｜可買 1｜不可追高觀察 0（不可買）｜淘汰 1", summary_message(messages))
        self.assertNotIn("其中僅追蹤 0 檔拆分", summary_message(messages))
        self.assertIn("淘汰 1 檔｜主因：弱反彈待確認｜詳情見未持倉卡", summary_message(messages))
        self.assertNotIn("建準｜等", summary_message(messages))
        self.assertNotIn("旺宏｜等", summary_message(messages))
        self.assertIn("【建準 2421】🟢 可買｜10%倉｜買點成立", unheld_message(messages))

    def test_v19_4_volume_blocked_non_weak_stock_enters_wait_volume(self):
        payload = {
            "stock_code": "2376",
            "price": 330,
            "change": 0.8,
            "price_source": "realtime",
            "daily_source": "yahoo",
            "result": {
                "decision": "WAIT",
                "action": 0,
                "rr": 1.6,
                "heat_state": "NORMAL",
                "trade_state": "NO_VOLUME",
                "structure_phase": "BREAKOUT_CONFIRM",
                "price_behavior": "NORMAL",
                "market_grade": "B",
                "volume_state": "WEAK",
                "volume_price_state": "COILING",
                "structure_state": "NORMAL",
                "entry_quality": "B",
                "confidence_score": 70,
                "breakout_distance": 1.2,
            },
            "holding": None,
            "structure_score": 4,
            "volume_ratio": 0.6,
        }

        messages = generator.formatTelegramMessages(
            {"技嘉": payload},
            "FULL DETAIL",
            None,
            None,
            "⏳ 觀望",
            datetime(2026, 5, 26),
            report_phase="盤中",
        )

        self.assertIn("未持倉 1｜可買 0｜不可追高觀察 0（不可買）｜僅追蹤 1（等量能）｜淘汰 0", summary_message(messages))
        self.assertIn("未持倉 1 檔僅追蹤，等觸發，不列入今日盤中交易執行", summary_message(messages))
        self.assertNotIn("1. 技嘉｜等量能｜不買，等量能回升", summary_message(messages))
        self.assertIn("【技嘉 2376】👀 等量能｜量能不足", unheld_message(messages))

    def test_v19_4_backtest_changes_tracking_order_only(self):
        weak_context = {
            "sample": 35,
            "win_rate": 42,
            "avg_return": -0.8,
        }
        strong_context = {
            "sample": 35,
            "win_rate": 62,
            "avg_return": 1.4,
        }

        def rr_payload(code, context):
            return {
                "stock_code": code,
                "price": 120,
                "change": 1.0,
                "price_source": "realtime",
                "daily_source": "yahoo",
                "result": {
                    "decision": "WAIT",
                    "action": 0,
                    "rr": 0.8,
                    "heat_state": "NORMAL",
                    "trade_state": "LATE_ENTRY",
                    "structure_phase": "BREAKOUT_CONFIRM",
                    "price_behavior": "NORMAL",
                    "market_grade": "B",
                    "volume_state": "NORMAL",
                    "volume_price_state": "NORMAL",
                    "structure_state": "NORMAL",
                    "entry_quality": "B",
                    "confidence_score": 70,
                    "breakout_distance": 1.2,
                },
                "holding": None,
                "backtest_context": context,
                "structure_score": 4,
                "volume_ratio": 1.0,
            }

        messages = generator.formatTelegramMessages(
            {
                "建準": rr_payload("2421", weak_context),
                "仁寶": rr_payload("2324", strong_context),
            },
            "FULL DETAIL",
            None,
            None,
            "⏳ 觀望",
            datetime(2026, 5, 26),
            report_phase="盤中",
        )

        self.assertIn("未持倉 2 檔僅追蹤，等觸發，不列入今日盤中交易執行", summary_message(messages))
        self.assertIn("未持倉 2｜可買 0｜不可追高觀察 0（不可買）｜僅追蹤 2（等RR修復）｜淘汰 0", summary_message(messages))
        self.assertNotIn("未持倉總數 2 檔", summary_message(messages))
        self.assertNotIn("其中僅追蹤 2 檔拆分", summary_message(messages))
        self.assertNotIn("【可買", summary_message(messages))
        self.assertIn("【仁寶 2324】👀 等RR修復｜RR不足", unheld_message(messages))
        self.assertIn("【建準 2421】👀 等RR修復｜RR不足", unheld_message(messages))

    def test_v19_3_3_holding_add_levels_display_explicit_add_actions(self):
        payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 122],
            {"shares": 100, "avg_price": 110},
            price=122,
            change=2.1,
        )
        payload["stock_code"] = "2376"
        payload["holding_decision"] = {
            "action": "加碼 20%",
            "level": "ADD_20",
            "note": "趨勢延續",
            "warning_price": 115,
            "hard_stop_price": 108,
            "allow_add": True,
        }

        card = generator.formatTelegramPositionCard("技嘉", payload)

        self.assertIn("【技嘉 2376】📌 加碼20", card)
        self.assertIn("決策：加碼 20%，趨勢延續", card)
        self.assertIn("條件：RR足夠，品質達標", card)

    def test_today_buy_holding_overrides_add_level_in_all_summary_surfaces(self):
        payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 122],
            {"shares": 100, "avg_price": 110},
            price=122,
            change=2.1,
        )
        payload["stock_code"] = "2376"
        payload["holding_decision"] = {
            "action": "加碼 20%",
            "level": "ADD_20",
            "note": "趨勢延續",
            "warning_price": 115,
            "hard_stop_price": 108,
            "allow_add": True,
        }
        payload["position_events"] = {"event_count": 1, "bought_shares": 100}
        payload["today_action"] = "BUY"

        card = generator.formatTelegramPositionCard("技嘉", payload)
        messages = generator.formatTelegramMessages(
            {"技嘉": payload},
            "FULL DETAIL",
            None,
            None,
            "⏳ 觀望",
            datetime(2026, 5, 27),
            report_phase="盤中",
        )

        self.assertIn("【技嘉 2376】📌 新倉風控觀察", card)
        self.assertIn("決策：新倉風控觀察，暫不加碼", card)
        self.assertIn("條件：守警戒價，跌破停損或轉弱優先風控", card)
        self.assertIn("1. 技嘉｜+10.91%｜新倉風控觀察｜盤中觀察修復狀況", summary_message(messages))
        self.assertNotIn("隔日計畫", summary_message(messages))
        self.assertNotIn("盤中觀察修復：技嘉收盤未修復則列入隔日降級檢查", summary_message(messages))
        self.assertNotIn("加碼20", card)
        self.assertNotIn("加碼 20%", card)
        self.assertNotIn("加碼20", summary_message(messages))
        self.assertNotIn("加碼 20%", summary_message(messages))

    def test_v20_4_cross_day_repair_promotes_prepare_without_buying(self):
        payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 121],
            None,
            price=121,
            change=2.1,
        )
        payload["stock_code"] = "2337"
        payload["result"].update({
            "decision": "WAIT",
            "action": 0,
            "market_grade": "B",
            "entry_quality": "B",
            "structure_phase": "BREAKOUT_NEAR",
            "price_behavior": "NORMAL",
            "heat_state": "NORMAL",
            "trade_state": "WAIT",
        })
        payload["cross_day_context"] = {
            "source_status": "ready",
            "previous_state": "eliminated",
            "previous_action": "observe",
            "previous_action_date": "2026-05-28",
            "consecutive_observe_days": 4,
            "repair_status": "improving",
            "failure_status": "cooling",
            "historical_evidence_weight": 1,
            "weight_reason": ["前次狀態修復中"],
            "dedupe_guard": "none",
            "source_of_truth": ["daily_signal_snapshot"],
            "forbidden_effects": ["cannot_flip_to_buy_alone"],
        }

        messages = generator.formatTelegramMessages(
            {"旺宏": payload},
            "FULL DETAIL",
            None,
            None,
            {"market_theme_evidence": {"theme_status": "absent", "level": "absent"}},
            datetime(2026, 5, 29),
            report_phase="盤中",
        )

        summary = summary_message(messages)
        unheld = unheld_message(messages)
        self.assertIn("【05/29 盤中｜v20.4.47】", summary)
        self.assertNotIn("僅追蹤：\n- 旺宏（修復中｜連續觀察 4 天，未達進場條件）", summary)
        self.assertNotIn("追蹤最強", summary)
        self.assertIn("未持倉 1｜可買 0｜不可追高觀察 1（不可買）｜淘汰 0", summary)
        self.assertIn("【旺宏 2337】👀 不可追高觀察", unheld)
        self.assertIn("歷史：前次 eliminated｜修復中｜連續觀察 4 天｜權重 +1", unheld)
        self.assertNotIn("旺宏｜可買", summary + unheld)

    def test_v20_4_cross_day_mixed_local_ready_source_has_no_generator_effect(self):
        payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 121],
            None,
            price=121,
            change=2.1,
        )
        payload["stock_code"] = "2337"
        payload["result"].update({
            "decision": "WAIT",
            "action": 0,
            "market_grade": "B",
            "entry_quality": "B",
            "structure_phase": "BREAKOUT_NEAR",
            "price_behavior": "NORMAL",
            "heat_state": "NORMAL",
            "trade_state": "WAIT",
        })
        payload["cross_day_context"] = {
            "source_status": "ready",
            "previous_state": "eliminated",
            "previous_action": "reduce",
            "previous_action_date": "2026-05-28",
            "consecutive_observe_days": 5,
            "repair_status": "improving",
            "failure_status": "cooling",
            "historical_evidence_weight": 2,
            "weight_reason": ["local fixture should not count"],
            "dedupe_guard": "prior_reduce_completed",
            "source_of_truth": ["position_events", "local_position_events"],
            "forbidden_effects": ["cannot_use_same_run_as_cross_day_memory"],
        }

        self.assertFalse(generator.cross_day_ready(payload))
        self.assertEqual(generator.cross_day_sort_adjustment(payload), 0)
        self.assertFalse(generator.cross_day_prepare_promotion(payload))

        messages = generator.formatTelegramMessages(
            {"旺宏": payload},
            "FULL DETAIL",
            None,
            None,
            {"market_theme_evidence": {"theme_status": "absent", "level": "absent"}},
            datetime(2026, 5, 29),
            report_phase="盤中",
        )

        output = "\n".join(messages)
        self.assertNotIn("連續觀察 5 天", output)
        self.assertNotIn("前次 eliminated", output)
        self.assertNotIn("權重 +2", output)
        self.assertNotIn("追蹤最強：\n- 旺宏 修復中", output)

    def test_v20_4_cross_day_take_profit_guard_suppresses_same_level_repeat(self):
        payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 130],
            {"shares": 100, "avg_price": 100, "realized_profit_taken_ratio": 0},
            price=130,
            change=9.9,
        )
        payload["stock_code"] = "2356"
        payload["holding_decision"] = {
            "action": "停利 25%",
            "level": "TAKE_PROFIT_25",
            "shares": 25,
            "note": "過熱延伸",
            "warning_price": 123,
            "hard_stop_price": 118,
            "allow_add": False,
        }
        payload["cross_day_context"] = {
            "source_status": "ready",
            "previous_state": "holding",
            "previous_action": "take_profit",
            "previous_action_date": "2026-05-29",
            "consecutive_observe_days": 0,
            "repair_status": "unchanged",
            "failure_status": "still_valid",
            "historical_evidence_weight": 0,
            "weight_reason": [],
            "dedupe_guard": "same_day_executed",
            "source_of_truth": ["position_events"],
            "forbidden_effects": ["cannot_flip_to_buy_alone"],
        }

        messages = generator.formatTelegramMessages(
            {"英業達": payload},
            "FULL DETAIL",
            None,
            None,
            "⏳ 觀望",
            datetime(2026, 5, 29),
            report_phase="盤中",
        )

        card = position_message(messages)
        summary = summary_message(messages)
        self.assertIn("【英業達 2356】📌 停利後觀察", card)
        self.assertIn("決策：停利後觀察，暫不加碼", card)
        self.assertIn("歷史停利已完成，同級不重複", card)
        self.assertIn("英業達｜+30.00%｜停利後觀察｜歷史停利已完成，等待新條件", summary)
        self.assertNotIn("英業達｜+30.00%｜停利｜", summary)
        self.assertNotIn("決策：停利 25%", card)

    def test_v20_4_cross_day_reduce_history_does_not_suppress_hard_risk_reduce(self):
        payload = render_payload(
            [120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 128, 127, 126, 125, 124, 123, 122, 118, 114, 110],
            {"shares": 100, "avg_price": 120},
            price=110,
            change=-5.5,
        )
        payload["stock_code"] = "3231"
        payload["holding_decision"] = {
            "action": "硬風控減碼 50%",
            "level": "REDUCE_50",
            "shares": 50,
            "note": "風控升級，跌破警戒仍需補足降風險",
            "warning_price": 116,
            "hard_stop_price": 108,
            "allow_add": False,
        }
        payload["cross_day_context"] = {
            "source_status": "ready",
            "previous_state": "holding",
            "previous_action": "reduce",
            "previous_action_date": "2026-05-28",
            "consecutive_observe_days": 0,
            "repair_status": "deteriorating",
            "failure_status": "invalidated",
            "historical_evidence_weight": -1,
            "weight_reason": ["前次減碼後仍轉弱"],
            "dedupe_guard": "prior_reduce_completed",
            "source_of_truth": ["position_events"],
            "forbidden_effects": ["cannot_flip_to_buy_alone", "cannot_override_hard_stop"],
        }

        messages = generator.formatTelegramMessages(
            {"緯創": payload},
            "FULL DETAIL",
            None,
            None,
            "⏳ 觀望",
            datetime(2026, 5, 29),
            report_phase="盤中",
        )

        card = position_message(messages)
        summary = summary_message(messages)
        self.assertIn("【緯創 3231】📌 硬風控減碼", card)
        self.assertIn("決策：硬風控減碼 50%，風控升級，跌破警戒仍需補足降風險", card)
        self.assertIn("條件：硬風控覆蓋，高於今日交易事件", card)
        self.assertIn("緯創｜-8.33%｜硬風控減碼｜無法重新站回突破區，繼續降低優先級", summary)
        self.assertNotIn("歷史減碼已完成", card + summary)
        self.assertNotIn("同級不重複", card + summary)
        self.assertNotIn("減碼後觀察", card + summary)

    def test_v20_4_today_buy_then_weakened_does_not_reverse_to_reduce_without_hard_stop(self):
        payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119],
            {"shares": 100, "avg_price": 118},
            price=119,
            change=-1.0,
        )
        payload["stock_code"] = "3017"
        payload["position_events"] = {"event_count": 1, "bought_shares": 100}
        payload["holding_decision"] = {
            "action": "減碼 25%",
            "level": "REDUCE_25",
            "shares": 25,
            "note": "轉弱",
            "warning_price": 112,
            "hard_stop_price": 108,
            "allow_add": False,
        }

        messages = generator.formatTelegramMessages(
            {"奇鋐": payload},
            "FULL DETAIL",
            None,
            None,
            "⏳ 觀望",
            datetime(2026, 5, 29),
            report_phase="盤中",
        )

        card = position_message(messages)
        summary = summary_message(messages)
        self.assertIn("【奇鋐 3017】📌 新倉風控觀察", card)
        self.assertIn("決策：新倉風控觀察，暫不加碼", card)
        self.assertIn("奇鋐｜+0.85%｜新倉風控觀察", summary)
        self.assertNotIn("奇鋐｜+0.85%｜減碼｜", summary)
        self.assertNotIn("決策：減碼 25%", card)

    def test_same_day_buy_hard_stop_is_not_exempted(self):
        payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 94],
            {"shares": 100, "avg_price": 100},
            price=94,
            change=-4.0,
        )
        payload["stock_code"] = "2303"
        payload["position_events"] = {"event_count": 1, "bought_shares": 100}
        payload["holding_decision"] = {
            "action": "減碼 50%",
            "level": "REDUCE_50",
            "shares": 50,
            "note": "跌破停損",
            "warning_price": 98,
            "hard_stop_price": 95,
            "allow_add": False,
        }

        messages = generator.formatTelegramMessages(
            {"聯電": payload},
            "FULL DETAIL",
            None,
            None,
            "⏳ 觀望",
            datetime(2026, 6, 3),
            report_phase="盤中",
        )

        card = position_message(messages)
        summary = summary_message(messages)
        self.assertIn("【聯電 2303】📌 減碼", card)
        self.assertIn("同日建倉後跌破 hard_stop，觸發當日減碼", card)
        self.assertIn("聯電｜-6.00%｜減碼", summary)
        self.assertNotIn("剛買入豁免", card + summary)

    def test_same_day_buy_entry_price_quick_stop_reduces_umc_fixture(self):
        payload = render_payload(
            [28, 28.2, 28.4, 28.6, 28.8, 29, 29.2, 29.4, 29.6, 29.8, 30, 29.8, 29.5, 29.2, 29, 28.8, 28.6, 28.4, 28.2, 27.4],
            {"shares": 1000, "avg_price": 28.5},
            price=27.4,
            change=-3.86,
        )
        payload["stock_code"] = "2303"
        payload["position_events"] = {"event_count": 1, "bought_shares": 1000}
        payload["holding_decision"] = {
            "action": "減碼 25%",
            "level": "REDUCE_25",
            "shares": 250,
            "note": "突破失敗",
            "warning_price": 27.8,
            "hard_stop_price": 26.5,
            "allow_add": False,
        }
        payload["result"].update({
            "price_behavior": "WEAK_REBOUND",
            "structure_phase": "FAILED_BREAKOUT",
            "market_grade": "D",
        })

        messages = generator.formatTelegramMessages(
            {"聯電": payload},
            "FULL DETAIL",
            None,
            None,
            "⏳ 觀望",
            datetime(2026, 6, 3),
            report_phase="盤中",
        )

        card = position_message(messages)
        summary = summary_message(messages)
        self.assertIn("【聯電 2303】📌 減碼", card)
        self.assertIn("條件：同日建倉後觸發快速止損 / 入場即錯", card)
        self.assertIn("聯電｜-3.86%｜減碼", summary)
        self.assertNotIn("新倉風控觀察", card + summary)
        self.assertNotIn("剛買入豁免", card + summary)

    def test_same_day_buy_entry_candle_low_quick_stop_reduces(self):
        payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 98.5],
            {"shares": 100, "avg_price": 100},
            price=98.5,
            change=-1.0,
        )
        payload["stock_code"] = "3017"
        payload["entry_candle_low"] = 99
        payload["position_events"] = {"event_count": 1, "bought_shares": 100}
        payload["holding_decision"] = {
            "action": "減碼 25%",
            "level": "REDUCE_25",
            "shares": 25,
            "note": "跌破入場 K 棒低點",
            "warning_price": 99.5,
            "hard_stop_price": 95,
            "allow_add": False,
        }

        messages = generator.formatTelegramMessages(
            {"奇鋐": payload},
            "FULL DETAIL",
            None,
            None,
            "⏳ 觀望",
            datetime(2026, 6, 3),
            report_phase="盤中",
        )

        self.assertIn("【奇鋐 3017】📌 減碼", position_message(messages))
        self.assertIn("同日建倉後觸發快速止損 / 入場即錯", position_message(messages))

    def test_same_day_buy_warning_only_stays_risk_watch(self):
        payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 98.5],
            {"shares": 100, "avg_price": 100},
            price=98.5,
            change=-1.0,
        )
        payload["stock_code"] = "3017"
        payload["position_events"] = {"event_count": 1, "bought_shares": 100}
        payload["holding_decision"] = {
            "action": "減碼 25%",
            "level": "REDUCE_25",
            "shares": 25,
            "note": "跌破警戒",
            "warning_price": 99,
            "hard_stop_price": 95,
            "allow_add": False,
        }

        messages = generator.formatTelegramMessages(
            {"奇鋐": payload},
            "FULL DETAIL",
            None,
            None,
            "⏳ 觀望",
            datetime(2026, 6, 3),
            report_phase="盤中",
        )

        card = position_message(messages)
        summary = summary_message(messages)
        self.assertIn("【奇鋐 3017】📌 新倉風控觀察", card)
        self.assertIn("奇鋐｜-1.50%｜新倉風控觀察", summary)
        self.assertNotIn("【奇鋐 3017】📌 減碼", card)
        self.assertNotIn("觸發當日減碼", card + summary)

    def test_post_market_add_plan_is_not_labeled_as_risk_control(self):
        payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 122],
            {"shares": 100, "avg_price": 110},
            price=122,
            change=2.1,
        )
        payload["stock_code"] = "2376"
        payload["holding_decision"] = {
            "action": "加碼 10%",
            "level": "ADD_10",
            "note": "小幅轉強",
            "warning_price": 115,
            "hard_stop_price": 108,
            "allow_add": True,
        }

        messages = generator.formatTelegramMessages(
            {"技嘉": payload},
            "FULL DETAIL",
            None,
            None,
            "⏳ 觀望",
            datetime(2026, 5, 28),
            report_phase="盤後",
        )

        summary = summary_message(messages)
        self.assertIn("【05/28 盤後｜v20.4.47】", summary)
        self.assertIn("📌 盤後簡報", summary)
        self.assertIn("結論：今日無有效新倉；既有持倉以收盤後風控觀察為主。", summary)
        self.assertIn("新增有效進場：無", summary)
        self.assertNotIn("今日交易：已建立新倉", summary)
        self.assertIn("明日前確認：觀察持倉是否跌破警戒。", summary)
        self.assertNotIn("技嘉｜明日風控｜加碼10", summary)
        self.assertNotIn("加碼後守警戒價，量價未延續則停止加碼", summary)

    def test_afterhours_brief_counts_today_buy_holdings_as_executed_new_positions(self):
        def today_buy_payload(code, qty, price):
            payload = render_payload(
                [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, price],
                {"shares": qty, "avg_price": price - 2},
                price=price,
                change=1.5,
            )
            payload["stock_code"] = code
            payload["holding_decision"] = {
                "action": "風控觀察",
                "level": "NEW_POSITION_RISK_WATCH",
                "note": "今日剛買入",
                "warning_price": price - 4,
                "hard_stop_price": price - 8,
                "allow_add": False,
            }
            payload["position_events"] = {"event_count": 1, "bought_shares": qty}
            payload["today_action"] = "BUY"
            return payload

        messages = generator.formatTelegramMessages(
            {
                "建準": today_buy_payload("2421", 1000, 120),
                "光寶科": today_buy_payload("2301", 1000, 118),
                "旺宏": today_buy_payload("2337", 2000, 116),
            },
            "FULL DETAIL",
            None,
            None,
            "⏳ 觀望",
            datetime(2026, 6, 1),
            report_phase="盤後",
        )

        card = position_message(messages)
        summary = summary_message(messages)

        self.assertIn("今日 買 1000股", card)
        self.assertIn("📌 盤後簡報", summary)
        self.assertIn("結論：今日交易已建立新倉 3 檔；新增有效進場：無。", summary)
        self.assertIn("今日交易：已建立新倉 3 檔（", summary)
        self.assertIn("建準", summary)
        self.assertIn("光寶科", summary)
        self.assertIn("旺宏", summary)
        self.assertIn("新增有效進場：無", summary)
        self.assertNotIn("今日無有效新倉", summary)

    def test_afterhours_today_buy_holding_explains_current_non_buy_by_source(self):
        def today_buy_payload(source):
            payload = render_payload(
                [110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 118],
                {"shares": 50, "avg_price": 116},
                price=118,
                change=-1.2,
            )
            payload["stock_code"] = "2301"
            payload["buy_source"] = source
            payload["position_events"] = {"event_count": 1, "bought_shares": 50}
            payload["today_action"] = "BUY" if source == "strategy_intraday" else ""
            payload["holding_decision"] = {
                "action": "風控觀察",
                "level": "NEW_POSITION_RISK_WATCH",
                "note": "今日剛買入",
                "warning_price": 112,
                "hard_stop_price": 108,
                "allow_add": False,
            }
            payload["result"].update({
                "decision": "WAIT",
                "action": 0,
                "entry_quality": "B",
                "structure_phase": "SHAKEOUT",
                "market_grade": "D",
                "volume_state": "NORMAL",
                "volume_price_state": "NORMAL",
                "structure_state": "NORMAL",
                "trade_state": "WAIT",
                "heat_state": "NORMAL",
                "breakout_state": "READY",
                "breakout_distance": 5.43,
            })
            payload["breakout_distance"] = 5.43
            return payload

        cases = [
            ("strategy_intraday", ["今日已執行", "盤後已不在買點", "不代表可繼續買"]),
            ("manual_or_ledger", ["手動/ledger", "非當前策略買點", "不代表可繼續買"]),
            ("unknown", ["來源未確認", "不得視為當前可買"]),
        ]

        for source, expected_terms in cases:
            with self.subTest(source=source):
                messages = generator.formatTelegramMessages(
                    {"光寶科": today_buy_payload(source)},
                    "FULL DETAIL",
                    None,
                    None,
                    "⏳ 觀望",
                    datetime(2026, 6, 1),
                    report_phase="盤後",
                )

                card = position_message(messages)
                brief = evidence_message(messages)
                rendered = "\n\n".join(messages)

                self.assertIn("【光寶科 2301】📌 新倉風控觀察", card)
                self.assertIn("今日 買 50股", card)
                self.assertIn("盤面：洗盤回測｜弱勢｜普通｜遠離突破（5.43%）", card)
                for term in expected_terms:
                    self.assertIn(term, card)
                self.assertIn("結論：今日交易已建立新倉 1 檔；新增有效進場：無。", brief)
                self.assertIn("今日交易：已建立新倉 1 檔（光寶科）", brief)
                self.assertNotIn("光寶科｜可買", rendered)
                self.assertNotIn("買點：可買", rendered)
                self.assertNotIn("推薦買入", rendered)

    def test_post_market_holding_risk_precedes_tomorrow_plan_without_duplicate_downgrade(self):
        def holding_payload(code, level, action, avg_price=124, price=122):
            payload = render_payload(
                [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, price],
                {"shares": 100, "avg_price": avg_price},
                price=price,
                change=-1.2,
            )
            payload["stock_code"] = code
            payload["holding_decision"] = {
                "action": action,
                "level": level,
                "note": "收盤未修復",
                "warning_price": 118,
                "hard_stop_price": 110,
                "allow_add": level.startswith("ADD_"),
            }
            if level == "NEW_POSITION_RISK_WATCH":
                payload["position_events"] = {"event_count": 1, "bought_shares": 100}
                payload["today_action"] = "BUY"
            return payload

        messages = generator.formatTelegramMessages(
            {
                "智原": holding_payload("3035", "NEW_POSITION_RISK_WATCH", "風控觀察"),
                "緯創": holding_payload("3231", "NEW_POSITION_RISK_WATCH", "風控觀察"),
                "技嘉": holding_payload("2376", "ADD_10", "加碼 10%", avg_price=110, price=122),
            },
            "FULL DETAIL",
            None,
            None,
            "⏳ 觀望",
            datetime(2026, 5, 28),
            report_phase="盤後",
        )

        summary = summary_message(messages)
        self.assertIn("【05/28 盤後｜v20.4.47】", summary)
        self.assertIn("📌 盤後簡報", summary)
        self.assertIn("結論：今日交易已建立新倉 2 檔；新增有效進場：無。", summary)
        self.assertIn("今日交易：已建立新倉 2 檔（智原、緯創）", summary)
        self.assertNotIn("今日無有效新倉", summary)
        self.assertIn("明日前確認：觀察持倉是否跌破警戒。", summary)
        self.assertNotIn("隔日計畫", summary)
        self.assertNotIn("收盤未修復，列入明日降級檢查：智原", summary)
        self.assertNotIn("收盤未修復，列入明日降級檢查：緯創", summary)

    def test_post_market_omits_empty_tomorrow_plan_when_only_holding_risk_exists(self):
        def risk_payload(code):
            payload = render_payload(
                [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 122],
                {"shares": 100, "avg_price": 124},
                price=122,
                change=-1.2,
            )
            payload["stock_code"] = code
            payload["holding_decision"] = {
                "action": "風控觀察",
                "level": "NEW_POSITION_RISK_WATCH",
                "note": "收盤未修復",
                "warning_price": 118,
                "hard_stop_price": 110,
                "allow_add": False,
            }
            payload["position_events"] = {"event_count": 1, "bought_shares": 100}
            payload["today_action"] = "BUY"
            return payload

        messages = generator.formatTelegramMessages(
            {
                "智原": risk_payload("3035"),
                "緯創": risk_payload("3231"),
            },
            "FULL DETAIL",
            None,
            None,
            "⏳ 觀望",
            datetime(2026, 5, 28),
            report_phase="盤後",
        )

        summary = summary_message(messages)
        self.assertIn("📌 盤後簡報", summary)
        self.assertIn("明日前確認：觀察持倉是否跌破警戒。", summary)
        self.assertNotIn("明日計畫 0", summary)
        self.assertNotIn("明日計畫：無新增下單", summary)
        self.assertNotIn("明日計畫\n無新增下單", summary)
        self.assertNotIn("隔日計畫", summary)

    def test_rejected_summary_shows_count_not_full_four_stock_names(self):
        def rejected_payload(code):
            return {
                "stock_code": code,
                "price": 81,
                "change": -2.0,
                "price_source": "realtime",
                "daily_source": "yahoo",
                "result": {
                    "decision": "WAIT",
                    "action": 0,
                    "rr": 2.0,
                    "heat_state": "NORMAL",
                    "trade_state": "WAIT",
                    "structure_phase": "WEAK_REBOUND",
                    "price_behavior": "WEAK_REBOUND",
                    "market_grade": "D",
                    "volume_state": "WEAK",
                    "volume_price_state": "COILING",
                    "structure_state": "WEAK",
                    "entry_quality": "D",
                    "confidence_score": 30,
                    "breakout_distance": 8,
                },
                "holding": None,
                "structure_score": 1,
                "volume_ratio": 0.5,
            }

        messages = generator.formatTelegramMessages(
            {
                "旺宏": rejected_payload("2337"),
                "群創": rejected_payload("3481"),
                "南亞科": rejected_payload("2408"),
                "仁寶": rejected_payload("2324"),
            },
            "FULL DETAIL",
            None,
            None,
            "⏳ 觀望",
            datetime(2026, 5, 27),
            report_phase="盤後",
        )

        summary_msg = summary_message(messages)
        self.assertIn("📌 盤後簡報", summary_msg)
        self.assertIn("未持倉標的等待下一交易日訊號", summary_msg)
        self.assertIn("【旺宏 2337】⛔ 淘汰", unheld_message(messages))
        self.assertIn("【群創 3481】⛔ 淘汰", unheld_message(messages))
        self.assertNotIn("旺宏", summary_msg)
        self.assertNotIn("群創", summary_msg)
        self.assertNotIn("南亞科", summary_msg)
        self.assertNotIn("仁寶", summary_msg)
        self.assertNotIn("淘汰 4：旺宏、群創、南亞科、仁寶", summary_msg)

    def test_post_reduce_watch_card_uses_sold_shares_fallback_without_sell_pct(self):
        payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119],
            {"shares": 110, "avg_price": 100},
            price=105,
            change=-1.0,
        )
        payload["stock_code"] = "3231"
        payload["result"].update({
            "structure_phase": "DISTRIBUTION",
            "price_behavior": "DISTRIBUTION_SPIKE",
            "volume_price_state": "DISTRIBUTION",
            "trend": "UP",
            "volume_state": "STRONG",
            "multi_day_bias": "MIXED",
            "decision": "WAIT",
        })
        payload["position_events"] = {"event_count": 1, "sold_shares": 40}

        card = generator.formatTelegramPositionCard("緯創", payload)
        decision = payload["holding_decision"]
        messages = generator.formatTelegramMessages(
            {"緯創": payload},
            "FULL DETAIL",
            None,
            None,
            "⏳ 觀望",
            datetime(2026, 5, 27),
            report_phase="盤後",
        )

        self.assertEqual(decision["level"], "POST_REDUCE_WATCH")
        self.assertIn("【緯創 3231】📌 減碼後觀察", card)
        self.assertIn("今日 賣 40股", card)
        self.assertIn("決策：減碼後觀察，暫不加碼", card)
        self.assertIn("今日已減碼約27%", decision["note"])
        self.assertIn("📌 盤後簡報", summary_message(messages))
        self.assertIn("既有持倉以收盤後風控觀察為主", summary_message(messages))
        self.assertNotIn("📌 減碼｜", card)
        self.assertNotIn("決策：減碼 25%", card)
        self.assertNotIn("緯創｜+5.00%｜減碼｜", summary_message(messages))

    def test_v19_3_3_profit_reduce_stop_detail_lines_are_direct_actions(self):
        base = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119],
            {"shares": 100, "avg_price": 120},
            price=108,
            change=-4,
        )
        base["stock_code"] = "3035"

        stop_payload = dict(base)
        stop_payload["holding_decision"] = {
            "action": "停損 100%",
            "level": "STOP_100",
            "note": "硬停損觸發",
            "warning_price": 114,
            "hard_stop_price": 110,
        }
        stop_card = generator.formatTelegramPositionCard("智原", stop_payload)
        self.assertIn("【智原 3035】📌 停損", stop_card)
        self.assertIn("決策：停損 100%，硬停損觸發", stop_card)
        self.assertIn("條件：停損優先，避免虧損擴大", stop_card)
        self.assertIn("原因：跌破停損線，避免虧損擴大", stop_card)
        self.assertIn("下一步：清出後不急回補，等重新出現買點", stop_card)

        reduce_payload = dict(base)
        reduce_payload["holding_decision"] = {
            "action": "減碼 25%",
            "level": "REDUCE_25",
            "note": "結構破壞，先降風險",
            "warning_price": 114,
            "hard_stop_price": 110,
        }
        reduce_card = generator.formatTelegramPositionCard("智原", reduce_payload)
        self.assertIn("【智原 3035】📌 減碼", reduce_card)
        self.assertIn("決策：減碼 25%，降低風險", reduce_card)
        self.assertIn("條件：結構轉弱或突破失敗，先降風險", reduce_card)
        self.assertIn("原因：突破失敗或結構轉弱，先降低風險", reduce_card)
        self.assertIn("下一步：若無法重新站回突破區，繼續降低優先級", reduce_card)

        profit_payload = dict(base)
        profit_payload["price"] = 140
        profit_payload["holding"] = {"shares": 100, "avg_price": 110}
        profit_payload["holding_decision"] = {
            "action": "停利 25%",
            "level": "TAKE_PROFIT_25",
            "note": "漲停過熱，保留核心倉",
            "warning_price": 133,
            "hard_stop_price": 126,
        }
        profit_card = generator.formatTelegramPositionCard("智原", profit_payload)
        self.assertIn("【智原 3035】📌 停利", profit_card)
        self.assertIn("決策：停利 25%，鎖定部分獲利", profit_card)
        self.assertIn("條件：高浮盈或過熱延伸，保留核心倉", profit_card)
        self.assertIn("原因：高浮盈且過熱延伸，先保留獲利", profit_card)
        self.assertIn("下一步：保留核心倉，等待冷卻後再評估", profit_card)

    def test_post_profit_watch_card_does_not_repeat_same_level_take_profit(self):
        payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 130],
            {"shares": 100, "avg_price": 100, "realized_profit_taken_ratio": 0.25},
            price=130,
            change=9.9,
        )
        payload["stock_code"] = "3035"

        card = generator.formatTelegramPositionCard("智原", payload)
        messages = generator.formatTelegramMessages(
            {"智原": payload},
            "FULL DETAIL",
            None,
            None,
            "⏳ 觀望",
            datetime(2026, 5, 27),
            report_phase="盤後",
        )

        self.assertIn("v20.4.47", summary_message(messages))
        self.assertEqual(payload["holding_decision"]["level"], "POST_PROFIT_WATCH")
        self.assertIn("【智原 3035】📌 停利後觀察", card)
        self.assertIn("決策：停利後觀察，暫不加碼", card)
        self.assertIn("同級停利已完成", card)
        self.assertIn("📌 盤後簡報", summary_message(messages))
        self.assertIn("既有持倉以收盤後風控觀察為主", summary_message(messages))
        self.assertNotIn("決策：停利 25%", card)

    def test_v20_2_2_same_day_executed_take_profit_stays_observation_across_summary(self):
        payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 130],
            {"shares": 188, "avg_price": 100, "realized_profit_taken_ratio": 0.25},
            price=130,
            change=5.2,
        )
        payload["stock_code"] = "2356"
        payload["position_events"] = {
            "event_count": 1,
            "sold_shares": 112,
            "sell_pct": 25,
            "shares_before": 300,
        }

        with patch.object(generator, "get_market_phase", return_value="盤中"):
            messages = generator.formatTelegramMessages(
                {"英業達": payload},
                "FULL DETAIL",
                None,
                None,
                "🟡 局部機會",
                datetime(2026, 5, 29),
            )

        card = position_message(messages)
        summary = summary_message(messages)

        self.assertIn("【05/29 盤中｜v20.4.47】", summary)
        self.assertEqual(payload["holding_decision"]["level"], "POST_PROFIT_WATCH")
        self.assertIn("【英業達 2356】📌 停利後觀察", card)
        self.assertIn("倉位：188股", card)
        self.assertIn("今日 賣 112股（25%）", card)
        self.assertIn("決策：停利後觀察，暫不加碼", card)
        self.assertIn("同級停利已完成", card)
        self.assertIn("英業達｜已執行｜今日已執行停利 112 股｜成交後剩餘 188 股｜同級停利已完成", summary)
        self.assertIn("1. 英業達｜停利後觀察｜成交後剩餘 188 股｜同級停利已完成", summary)
        self.assertNotIn("英業達｜+30.00%｜停利｜", summary)
        self.assertNotIn("決策：停利 25%", card)

    def test_v20_2_3_unexecuted_next_profit_level_can_still_surface_as_pending_sell_action(self):
        payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 130],
            {"shares": 150, "avg_price": 100, "realized_profit_taken_ratio": 0.5},
            price=130,
            change=9.9,
        )
        payload["stock_code"] = "2356"

        with patch.object(generator, "get_market_phase", return_value="盤中"):
            messages = generator.formatTelegramMessages(
                {"英業達": payload},
                "FULL DETAIL",
                None,
                None,
                "🟡 局部機會",
                datetime(2026, 5, 29),
            )

        card = position_message(messages)
        summary = summary_message(messages)
        pending_context = f"本次建議 {payload['holding_decision']['shares']} 股｜剩餘 150 股"

        self.assertEqual(payload["holding_decision"]["level"], "TAKE_PROFIT_25")
        self.assertEqual(generator.position_summary_action("英業達", payload), "第二段停利")
        self.assertIn("【英業達 2356】📌 第二段停利", card)
        self.assertIn(f"決策：第二段停利，{pending_context}", card)
        self.assertIn(f"英業達｜+30.00%｜第二段停利｜{pending_context}", summary)
        self.assertIn(f"1. 英業達｜+30.00%｜第二段停利｜{pending_context}", summary)
        self.assertNotIn("已執行｜今日已執行停利", summary)
        self.assertNotIn("英業達｜+30.00%｜停利｜保留核心倉", summary)

    def test_v20_2_3_completed_same_day_second_take_profit_uses_db_execution_data(self):
        payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 130],
            {"shares": 225, "avg_price": 100, "realized_profit_taken_ratio": 0.25},
            price=130,
            change=5.2,
        )
        payload["stock_code"] = "2356"
        payload["db_execution"] = {
            "event_type": "TAKE_PROFIT",
            "action_label": "停利 25%",
            "shares_delta": -75,
        }
        payload["holding_decision"] = {
            "action": "停利 25%",
            "level": "TAKE_PROFIT_25",
            "shares": 56,
            "note": "過熱延伸再次達停利條件",
            "warning_price": 123,
            "hard_stop_price": 118,
            "allow_add": False,
        }

        with patch.object(generator, "get_market_phase", return_value="盤中"):
            messages = generator.formatTelegramMessages(
                {"英業達": payload},
                "FULL DETAIL",
                None,
                None,
                "🟡 局部機會",
                datetime(2026, 5, 29),
            )

        card = position_message(messages)
        summary = summary_message(messages)
        executed_context = "今日已賣 75 股｜剩餘 225 股｜第二段已執行"

        self.assertEqual(generator.position_summary_action("英業達", payload), "第二段停利後觀察")
        self.assertIn("【05/29 盤中｜v20.4.47】", summary)
        self.assertIn("【英業達 2356】📌 第二段停利後觀察", card)
        self.assertIn("今日 賣 75股", card)
        self.assertIn(f"決策：第二段停利後觀察，{executed_context}", card)
        self.assertIn("條件：今日已執行，避免重複賣出", card)
        self.assertIn(f"英業達｜已執行｜{executed_context}", summary)
        self.assertIn(f"1. 英業達｜第二段停利後觀察｜{executed_context}", summary)
        self.assertNotIn("今日 無", card)
        self.assertNotIn("本次建議 56 股", summary + card)
        self.assertNotIn("英業達｜+30.00%｜第二段停利｜", summary)
        self.assertNotIn("英業達｜+30.00%｜停利｜保留核心倉", summary)

    def test_holiday_second_take_profit_uses_latest_trading_day_execution_memory(self):
        payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 130],
            {"shares": 225, "avg_price": 100, "realized_profit_taken_ratio": 0.5},
            price=130,
            change=5.2,
        )
        payload["stock_code"] = "2356"
        payload["holding_decision"] = {
            "action": "停利 25%",
            "level": "TAKE_PROFIT_25",
            "shares": 56,
            "note": "過熱延伸再次達停利條件",
            "warning_price": 123,
            "hard_stop_price": 118,
            "allow_add": False,
        }
        payload["cross_day_context"] = {
            "source_status": "ready",
            "source_of_truth": ["position_events"],
            "previous_action": "take_profit",
            "previous_action_date": "2026-05-29",
            "dedupe_guard": "prior_take_profit_completed",
            "execution_memory": {
                "source": "position_events",
                "latest_trade_date": "2026-05-29",
                "sell_deltas": [-112, -75],
                "sold_shares": 187,
                "labels": ["停利 25%"],
            },
        }

        with patch.object(
            generator,
            "load_confirmed_market_theme_evidence",
            return_value={"status": "missing-source", "confirmed": False, "reason": "test", "rows": []},
        ):
            messages = generator.formatTelegramMessages(
                {"英業達": payload},
                "FULL DETAIL",
                None,
                None,
                "🟡 局部機會",
                datetime(2026, 5, 31),
                report_phase="假日",
            )

        card = position_message(messages)
        summary = summary_message(messages)
        context = (
            "production latest_trade_date=2026-05-29｜已賣出 -112、-75"
            "｜realized_profit_taken_ratio=0.5｜剩餘 225 股｜第二段已執行"
        )

        self.assertEqual(generator.position_summary_action("英業達", payload), "第二段停利後觀察")
        self.assertIn("【05/31 假日｜v20.4.47】", summary)
        self.assertIn("【英業達 2356】📌 第二段停利後觀察", card)
        self.assertIn("今日 最近交易日賣 187股", card)
        self.assertIn(context, card)
        self.assertNotIn(f"英業達｜已執行｜{context}", summary)
        self.assertIn("持倉：依第一則既有卡片處理，不新增第二個主行動。", summary)
        self.assertNotIn("資料依據", summary)
        self.assertNotIn("資料依據", summary)
        self.assertNotIn(f"1. 英業達｜已執行｜{context}", summary)
        self.assertNotIn("第二段停利 本次建議 56 股", summary + card)
        self.assertNotIn("本次建議 56 股", summary + card)
        self.assertNotIn("英業達｜明日風控｜第二段停利", summary)
        self.assertNotIn("英業達｜+30.00%｜第二段停利｜", summary)

    def test_holiday_second_take_profit_fails_closed_when_execution_memory_missing(self):
        memory_cases = [
            None,
            {
                "source": "position_events",
                "latest_trade_date": "2026-05-29",
                "sell_deltas": [],
                "sold_shares": 0,
                "labels": ["停利 25%"],
            },
        ]

        for execution_memory in memory_cases:
            with self.subTest(execution_memory=execution_memory):
                payload = render_payload(
                    [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 130],
                    {"shares": 225, "avg_price": 100, "realized_profit_taken_ratio": 0.5},
                    price=130,
                    change=5.2,
                )
                payload["stock_code"] = "2356"
                payload["holding_decision"] = {
                    "action": "停利 25%",
                    "level": "TAKE_PROFIT_25",
                    "shares": 56,
                    "note": "過熱延伸再次達停利條件",
                    "warning_price": 123,
                    "hard_stop_price": 118,
                    "allow_add": False,
                }
                payload["cross_day_context"] = {
                    "source_status": "ready",
                    "source_of_truth": ["position_events"],
                    "previous_action": "take_profit",
                    "previous_action_date": "2026-05-29",
                    "dedupe_guard": "prior_take_profit_completed",
                    "execution_memory": execution_memory,
                }

                with patch.object(
                    generator,
                    "load_confirmed_market_theme_evidence",
                    return_value={"status": "missing-source", "confirmed": False, "reason": "test", "rows": []},
                ):
                    messages = generator.formatTelegramMessages(
                        {"英業達": payload},
                        "FULL DETAIL",
                        None,
                        None,
                        "🟡 局部機會",
                        datetime(2026, 5, 31),
                        report_phase="假日",
                    )

                card = position_message(messages)
                summary = summary_message(messages)
                rendered = summary + card

                self.assertEqual(generator.position_summary_action("英業達", payload), "停利記憶不足")
                self.assertIn("停利記憶不足", rendered)
                self.assertIn("停利記憶不足，暫不輸出賣出股數", rendered)
                self.assertIn("execution memory 不足，fail closed 不輸出停利股數", card)
                self.assertNotIn("第二段停利 本次建議 56 股", rendered)
                self.assertNotIn("本次建議 56 股", rendered)
                self.assertNotIn("英業達｜明日風控｜第二段停利", summary)
                self.assertNotIn("明日風控｜第二段停利", summary)

    def test_v20_2_3_partial_same_day_second_take_profit_uses_local_execution_data(self):
        payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 130],
            {"shares": 280, "avg_price": 100, "realized_profit_taken_ratio": 0.25},
            price=130,
            change=5.2,
        )
        payload["stock_code"] = "2356"
        payload["local_executions"] = [
            {"action_label": "停利 25%", "shares": 20},
        ]
        payload["holding_decision"] = {
            "action": "停利 25%",
            "level": "TAKE_PROFIT_25",
            "shares": 56,
            "note": "過熱延伸再次達停利條件",
            "warning_price": 123,
            "hard_stop_price": 118,
            "allow_add": False,
        }

        with patch.object(generator, "get_market_phase", return_value="盤中"):
            messages = generator.formatTelegramMessages(
                {"英業達": payload},
                "FULL DETAIL",
                None,
                None,
                "🟡 局部機會",
                datetime(2026, 5, 29),
            )

        card = position_message(messages)
        summary = summary_message(messages)
        remaining_context = "第二段停利剩餘建議 36 股｜今日已賣 20 股｜原建議 56 股｜剩餘持倉 280 股"

        self.assertEqual(generator.position_summary_action("英業達", payload), "第二段停利剩餘建議")
        self.assertIn("【英業達 2356】📌 第二段停利剩餘建議", card)
        self.assertIn("今日 賣 20股", card)
        self.assertIn(f"決策：{remaining_context}", card)
        self.assertIn(f"英業達｜+30.00%｜第二段停利剩餘建議｜{remaining_context}", summary)
        self.assertIn(f"1. 英業達｜+30.00%｜第二段停利剩餘建議｜{remaining_context}", summary)
        self.assertNotIn("今日 無", card)
        self.assertNotIn("本次建議 56 股", summary + card)

    def test_intraday_v20_0_10_execution_contract(self):
        holding_payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 130],
            {"shares": 75, "avg_price": 100, "realized_profit_taken_ratio": 0.25},
            price=130,
            change=5.2,
        )
        holding_payload["stock_code"] = "2356"
        holding_payload["position_events"] = {"event_count": 1, "sold_shares": 25, "sell_pct": 25}

        buy_payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119],
            None,
            price=119,
            change=2.1,
        )
        buy_payload["stock_code"] = "2301"
        buy_payload["result"].update({
            "decision": "BUY",
            "action": 0.6,
            "entry_quality": "A",
            "heat_state": "NORMAL",
            "trade_state": "READY",
            "rr": 1.8,
            "market_grade": "A",
            "market_regime": "RISK_ON",
        })

        rejected_payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119],
            None,
            price=119,
            change=7.23,
        )
        rejected_payload["stock_code"] = "2337"
        rejected_payload["result"].update({
            "decision": "NO_TRADE",
            "action": 0,
            "structure_phase": "WEAK_REBOUND",
            "price_behavior": "WEAK_REBOUND",
            "market_grade": "D",
            "volume_state": "WEAK",
            "rr": 2.44,
        })

        with patch.object(generator, "get_market_phase", return_value="盤中"):
            messages = generator.formatTelegramMessages(
                {
                    "英業達": holding_payload,
                    "光寶科": buy_payload,
                    "旺宏": rejected_payload,
                },
                "FULL DETAIL",
                "光寶科",
                88,
                "🟡 局部機會",
                datetime(2026, 5, 28),
                strategy_evidence_summary=AVAILABLE_STRATEGY_EVIDENCE,
            )

        summary = summary_message(messages)
        position = position_message(messages)
        unheld = unheld_message(messages)

        self.assertIn("【05/28 盤中｜v20.4.47】", summary)
        self.assertIn("✅ 今日盤中交易執行", summary)
        self.assertNotIn("明日執行", summary)
        self.assertIn("市場：中性觀察 R2｜執行動作 1（停利）｜新倉建議 1｜今日新建倉 0｜持倉風控 1｜未持倉 2（可買1/僅追蹤0/淘汰1）", summary)
        self.assertIn("光寶科 可買（分批，不追價）", summary)
        self.assertIn("英業達｜已執行｜今日已執行停利 25 股｜成交後剩餘 75 股｜同級停利已完成", summary)
        self.assertIn("已執行（不重複下單）", summary)
        self.assertNotIn("英業達｜停利 25%", summary)
        self.assertNotIn("待執行：停利 25%", summary)
        self.assertNotIn("可買 60%倉", summary)
        self.assertIn("【光寶科 2301】🟢 可買｜首筆最多 30%，總上限 60%｜買點成立", unheld)
        self.assertIn("買點：可買｜首筆最多 30%，總上限 60%｜分批，不追價", unheld)
        self.assertIn("盤中觸發：", unheld)
        self.assertNotIn("可買｜60%倉", unheld)
        self.assertNotIn("買點：可買｜建議 60%倉｜現在可分批", unheld)
        self.assertNotIn("建議 60%倉", unheld)
        self.assertIn("【旺宏 2337】⛔ 淘汰｜弱反彈待確認", unheld)
        self.assertIn("買點：不可買，等結構修復", unheld)

    def test_intraday_v20_0_11_followup_review_contract(self):
        holding_payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 130],
            {"shares": 75, "avg_price": 100, "realized_profit_taken_ratio": 0.25},
            price=130,
            change=5.2,
        )
        holding_payload["stock_code"] = "2356"
        holding_payload["position_events"] = {"event_count": 1, "sold_shares": 25, "sell_pct": 25}

        watch_payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119],
            None,
            price=119,
            change=1.2,
        )
        watch_payload["stock_code"] = "2421"
        watch_payload["result"].update({
            "decision": "WAIT",
            "action": 0,
            "trade_state": "LATE_ENTRY",
            "rr": 0.7,
            "market_grade": "A",
        })

        innolux_payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 112],
            None,
            price=112,
            change=-5.86,
        )
        innolux_payload["stock_code"] = "3481"
        innolux_payload["result"].update({
            "decision": "FAIL",
            "action": 0,
            "structure_phase": "FAILED_BREAKOUT",
            "heat_state": "EXTREME",
            "trade_state": "AVOID",
            "rr": 0,
        })

        liteon_payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 110],
            None,
            price=110,
            change=-6.2,
        )
        liteon_payload["stock_code"] = "2301"
        liteon_payload["result"].update({
            "decision": "FAIL",
            "action": 0,
            "structure_phase": "FAILED_BREAKOUT",
            "price_behavior": "NORMAL",
            "heat_state": "NORMAL",
            "trade_state": "WAIT",
            "rr": 0.45,
        })

        with patch.object(generator, "get_market_phase", return_value="盤中"):
            messages = generator.formatTelegramMessages(
                {
                    "英業達": holding_payload,
                    "建準": watch_payload,
                    "群創": innolux_payload,
                    "光寶科": liteon_payload,
                },
                "FULL DETAIL",
                None,
                None,
                "🟡 盤中觀察",
                datetime(2026, 5, 28),
            )

        summary = summary_message(messages)
        position = position_message(messages)
        unheld = unheld_message(messages)

        self.assertIn("【05/28 盤中｜v20.4.47】", summary)
        self.assertIn("市場：進攻偏熱 R3｜執行動作 1（停利）｜今日新建倉 0｜持倉風控 1｜未持倉 3（僅追蹤1/淘汰2）", summary)
        self.assertIn("新倉：無有效進場", summary)
        self.assertNotIn("無新增下單", summary)
        self.assertIn("已執行（不重複下單）", summary)
        self.assertIn("英業達｜已執行｜今日已執行停利 25 股｜成交後剩餘 75 股｜同級停利已完成", summary)
        self.assertEqual(
            summary.count("英業達｜已執行｜今日已執行停利 25 股｜成交後剩餘 75 股｜同級停利已完成"),
            1,
        )
        self.assertIn("1. 英業達｜停利後觀察｜成交後剩餘 75 股｜同級停利已完成", summary)
        self.assertIn("持倉風控檢查", summary)
        self.assertNotIn("今日盤中執行清單", summary)
        self.assertNotIn("明日未修復", summary)
        self.assertNotIn("隔日未修復", summary)
        self.assertNotIn("待執行｜減碼 25%", summary)
        self.assertNotIn("明日未修復", position)
        self.assertNotIn("隔日未修復", position)
        self.assertIn("未持倉 3｜僅追蹤 1（等RR修復）｜淘汰 2", summary)
        self.assertIn("淘汰 2 檔｜主因：突破失敗｜詳情見未持倉卡", summary)
        self.assertIn("【群創 3481】⛔ 淘汰｜突破失敗", unheld)
        self.assertIn("原因：前次可買條件已失效：突破失敗或跌破進場條件｜補充：追價風險 / 過熱、RR不可用，不作主因", unheld)
        self.assertIn("【光寶科 2301】⛔ 淘汰｜突破失敗", unheld)
        self.assertIn("前次可買條件已失效：突破失敗或跌破進場條件", unheld)

    def test_intraday_v20_0_12_separates_mainline_from_execution(self):
        holding_payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 126],
            {"shares": 100, "avg_price": 100},
            price=126,
            change=2.4,
        )
        holding_payload["stock_code"] = "2330"
        holding_payload["holding_decision"] = {
            "action": "核心續抱",
            "level": "HOLD_CORE",
            "note": "高浮盈回落，暫不加碼",
            "warning_price": 118,
            "hard_stop_price": 112,
            "allow_add": False,
        }

        pullback_payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 126],
            None,
            price=126,
            change=3.1,
        )
        pullback_payload["stock_code"] = "3661"
        pullback_payload["result"].update({
            "decision": "WAIT",
            "action": 0,
            "breakout_distance": 7.5,
            "rr": 1.8,
            "market_grade": "A",
            "heat_state": "NORMAL",
            "trade_state": "WAIT",
        })

        hot_payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 132],
            None,
            price=132,
            change=6.4,
        )
        hot_payload["stock_code"] = "2308"
        hot_payload["result"].update({
            "decision": "WAIT",
            "action": 0,
            "breakout_distance": 1,
            "price_behavior": "NORMAL",
            "heat_state": "HOT",
            "trade_state": "EXTENDED",
            "rr": 1.4,
            "market_grade": "A",
        })

        rejected_payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 111],
            None,
            price=111,
            change=-4.8,
        )
        rejected_payload["stock_code"] = "0000"
        rejected_payload["result"].update({
            "decision": "FAIL",
            "action": 0,
            "structure_phase": "FAILED_BREAKOUT",
            "heat_state": "EXTREME",
            "trade_state": "AVOID",
            "rr": 0.4,
            "market_grade": "A",
        })

        missing_production_evidence = {
            "status": "missing-source",
            "confirmed": False,
            "source_of_truth": "production_db",
            "source_family": "production_db",
            "source_status": "missing-source",
            "reason": "test isolated production source missing",
            "sources": [],
            "rows": [],
        }

        with patch.object(generator, "get_market_phase", return_value="盤中"), patch.object(
            generator,
            "load_confirmed_market_theme_evidence",
            return_value=missing_production_evidence,
        ):
            messages = generator.formatTelegramMessages(
                {
                    "台積電": holding_payload,
                    "世芯-KY": pullback_payload,
                    "台達電": hot_payload,
                    "範例股": rejected_payload,
                },
                "FULL DETAIL",
                None,
                None,
                "market_theme_evidence:confirmed｜AI 主線偏多",
                datetime(2026, 5, 28),
            )

        summary = summary_message(messages)
        position = position_message(messages)
        unheld = unheld_message(messages)

        self.assertIn("【05/28 盤中｜v20.4.47】", summary)
        self.assertNotIn("資料依據", summary)
        self.assertNotIn("證據：production 來源不足，不作確認。", summary)
        self.assertNotIn("詳情：runtime 觀察僅供診斷，非確認來源。", summary)
        self.assertIn("🧭 主線：市場偏多但買點未成立。", summary)
        self.assertIn("🧭 執行：新增買點未成立，先等回測，不追高。", summary)
        self.assertIn("新倉：無有效進場", summary)
        self.assertLess(
            summary.index("決策簡報"),
            summary.index("市場：進攻偏熱 R3"),
        )
        self.assertNotIn("🧭 主線：AI / 電子供應鏈仍偏多。", summary)
        self.assertIn("新倉：無有效進場", summary)
        self.assertIn("未持倉 2 檔僅追蹤，等觸發，不列入今日盤中交易執行", summary)
        self.assertNotIn("強勢準備：", summary)
        self.assertIn("未持倉 3｜可買 0｜不可追高觀察 0（不可買）｜僅追蹤 2（等冷卻1/等回測1）｜淘汰 1", summary)
        self.assertIn("僅追蹤 2（等冷卻1/等回測1）", summary)
        self.assertIn("淘汰 1 檔｜主因：突破失敗｜詳情見未持倉卡", summary)
        self.assertIn("【台積電 2330】📌 核心續抱", position)
        self.assertIn("決策：核心續抱，暫不加碼", position)
        self.assertIn("下一步：保留核心倉，觀察是否轉弱", position)
        self.assertIn("台積電｜+26.00%｜核心續抱｜守警戒價，觀察是否轉弱", summary)
        self.assertEqual(generator.position_summary_note("台積電", holding_payload), "現有持倉保留，按風控續抱；新增倉位等觸發")
        self.assertNotIn("主線持倉保留", summary + position)
        self.assertIn("【世芯-KY 3661】⏳ 等回測｜遠離觸發", unheld)
        self.assertIn("買點：不買，等回測", unheld)
        self.assertIn("【台達電 2308】⏳ 等冷卻｜過熱觀察", unheld)
        self.assertIn("買點：不買，等冷卻", unheld)
        self.assertIn("【範例股 0000】⛔ 淘汰｜突破失敗", unheld)
        self.assertIn("買點：不可買，等重新轉強", unheld)
        self.assertIn("產業：未判斷產業多空", unheld)
        self.assertNotIn("不代表看空產業", unheld)
        self.assertNotIn("今天可進場追", summary)
        self.assertNotIn("可加碼", summary + position)
        self.assertNotIn("產業轉空", summary + unheld)

    def test_intraday_v20_0_12_hot_market_without_ai_evidence_uses_neutral_mainline(self):
        hot_payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 132],
            None,
            price=132,
            change=6.4,
        )
        hot_payload["stock_code"] = "1216"
        hot_payload["result"].update({
            "decision": "WAIT",
            "action": 0,
            "breakout_distance": 1,
            "price_behavior": "NORMAL",
            "heat_state": "HOT",
            "trade_state": "EXTENDED",
            "rr": 1.4,
            "market_grade": "A",
        })

        pullback_payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 126],
            None,
            price=126,
            change=3.1,
        )
        pullback_payload["stock_code"] = "2603"
        pullback_payload["result"].update({
            "decision": "WAIT",
            "action": 0,
            "breakout_distance": 7.5,
            "rr": 1.8,
            "market_grade": "A",
            "heat_state": "NORMAL",
            "trade_state": "WAIT",
        })

        with patch.object(generator, "get_market_phase", return_value="盤中"):
            messages = generator.formatTelegramMessages(
                {
                    "食品甲": hot_payload,
                    "航運乙": pullback_payload,
                },
                "FULL DETAIL",
                None,
                None,
                "🟢 市場偏強",
                datetime(2026, 5, 28),
            )

        summary = summary_message(messages)

        self.assertIn("市場：進攻偏熱 R3｜執行動作 0｜今日新建倉 0｜持倉風控 0｜未持倉 2（僅追蹤2/淘汰0）", summary)
        self.assertIn("🧭 主線：市場偏多但買點未成立。", summary)
        self.assertIn("🧭 執行：新增買點未成立，先等回測，不追高。", summary)
        self.assertNotIn("AI / 電子供應鏈仍偏多", summary)
        self.assertNotIn("AI 主線", summary)
        self.assertNotIn("電子供應鏈", summary)

    def test_v20_2_4_r3_hot_market_adds_prepare_layer_without_buying(self):
        limit_payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 132],
            None,
            price=132,
            change=9.8,
        )
        limit_payload["stock_code"] = "0001"
        limit_payload["result"].update({
            "decision": "WAIT",
            "action": 0,
            "price_behavior": "LIMIT_LOCK",
            "heat_state": "EXTREME",
            "trade_state": "AVOID",
            "rr": 1.6,
            "market_grade": "A",
            "entry_quality": "A",
        })

        hot_payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 128],
            None,
            price=128,
            change=6.1,
        )
        hot_payload["stock_code"] = "0002"
        hot_payload["result"].update({
            "decision": "WAIT",
            "action": 0,
            "price_behavior": "NORMAL",
            "heat_state": "HOT",
            "trade_state": "EXTENDED",
            "rr": 1.3,
            "market_grade": "A",
            "entry_quality": "A",
        })

        near_breakout_payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 121],
            None,
            price=121,
            change=2.0,
        )
        near_breakout_payload["stock_code"] = "0003"
        near_breakout_payload["result"].update({
            "decision": "WAIT",
            "action": 0,
            "breakout_distance": 2,
            "price_behavior": "NORMAL",
            "heat_state": "NORMAL",
            "trade_state": "WAIT",
            "structure_phase": "BREAKOUT_NEAR",
            "rr": 1.5,
            "market_grade": "A",
            "entry_quality": "A",
        })

        rr_payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 120],
            None,
            price=120,
            change=1.1,
        )
        rr_payload["stock_code"] = "0004"
        rr_payload["result"].update({
            "decision": "WAIT",
            "action": 0,
            "price_behavior": "NORMAL",
            "heat_state": "NORMAL",
            "trade_state": "LATE_ENTRY",
            "rr": 0.8,
            "market_grade": "B",
        })

        rejected_payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 108],
            None,
            price=108,
            change=-4.1,
        )
        rejected_payload["stock_code"] = "0005"
        rejected_payload["result"].update({
            "decision": "FAIL",
            "action": 0,
            "structure_phase": "FAILED_BREAKOUT",
            "rr": 0.7,
            "market_grade": "A",
        })

        messages = generator.formatTelegramMessages(
            {
                "A": limit_payload,
                "B": hot_payload,
                "C": near_breakout_payload,
                "D": rr_payload,
                "E": rejected_payload,
            },
            "FULL DETAIL",
            None,
            None,
            {"market_theme_evidence": {"theme_status": "absent", "level": "absent"}},
            datetime(2026, 5, 29),
            report_phase="盤中",
        )

        summary = summary_message(messages)
        unheld = unheld_message(messages)

        self.assertIn("【05/29 盤中｜v20.4.47】", summary)
        self.assertIn("市場：進攻偏熱 R3｜執行動作 0｜今日新建倉 0｜持倉風控 0｜未持倉 5（僅追蹤3/淘汰1）", summary)
        self.assertNotIn("市場/結論：進攻偏熱｜R3；R3 進攻偏熱", summary)
        self.assertNotIn("資料依據", summary)
        self.assertNotIn("證據：production 來源不足，不作確認。", summary)
        self.assertNotIn("詳情：runtime 觀察僅供診斷，非確認來源。", summary)
        self.assertIn("強勢準備：\n- 突破回測：C 待觸發，不追高", summary)
        self.assertNotIn("- 漲停鎖價：A", summary)
        self.assertNotIn("- 過熱降溫：B", summary)
        self.assertIn("未持倉 5｜可買 0｜不可追高觀察 1（不可買）｜僅追蹤 3（等冷卻1/等回測1/等RR修復1）｜淘汰 1", summary)
        self.assertIn("僅追蹤 3（等冷卻1/等回測1/等RR修復1）", summary)
        self.assertIn("【A 0001】⏳ 等回測｜漲停不追", unheld)
        self.assertIn("買點：不買，等回測", unheld)
        self.assertIn("【B 0002】⏳ 等冷卻｜過熱觀察", unheld)
        self.assertIn("買點：不買，等冷卻", unheld)
        self.assertIn("【C 0003】👀 不可追高觀察｜突破回測", unheld)
        self.assertIn("買點：待觸發，不追高", unheld)
        self.assertNotIn("市場 / 題材證據：absent", summary)
        self.assertNotIn("市場沒有證據", summary)
        self.assertNotIn("題材不存在", summary)
        self.assertNotIn("A｜可買", summary + unheld)
        self.assertNotIn("B｜可買", summary + unheld)
        self.assertNotIn("C｜可買", summary + unheld)

    def test_unheld_funnel_overheat_prepare_stays_tracking_but_normal_prepare_remains(self):
        def make_payload(overrides):
            payload = render_payload(
                [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 122],
                None,
                price=122,
                change=2.4,
            )
            payload["result"].update({
                "decision": "WAIT",
                "action": 0,
                "price_behavior": "NORMAL",
                "heat_state": "NORMAL",
                "trade_state": "WAIT",
                "rr": 1.5,
                "market_grade": "A",
                "entry_quality": "A",
            })
            payload["result"].update(overrides)
            return payload

        overheat_rr_blocked = make_payload({
            "heat_state": "HOT",
            "trade_state": "EXTENDED",
            "rr": 0,
        })
        hot_prepare = make_payload({
            "heat_state": "HOT",
            "trade_state": "EXTENDED",
            "rr": 1.4,
        })
        overheat_label_prepare = make_payload({
            "trade_state": "EXTENDED",
            "rr": 1.4,
        })
        normal_prepare = make_payload({
            "structure_phase": "BREAKOUT_NEAR",
            "breakout_distance": 2,
        })

        self.assertTrue(generator.should_show_overheat_rr_blocker(overheat_rr_blocked["result"], holding=False))
        self.assertEqual(generator.strong_prepare_bucket(overheat_label_prepare)[0], "過熱降溫")
        self.assertEqual(generator.unheld_funnel_state("RR過熱", overheat_rr_blocked, market_mode="進攻偏熱"), "等冷卻")
        self.assertEqual(generator.unheld_funnel_state("熱度過高", hot_prepare, market_mode="進攻偏熱"), "等冷卻")
        self.assertEqual(generator.unheld_funnel_state("標籤過熱", overheat_label_prepare, market_mode="進攻偏熱"), "等冷卻")
        self.assertEqual(generator.unheld_funnel_state("普通強勢", normal_prepare, market_mode="進攻偏熱"), "可準備")

    def test_low_volume_limit_up_prepare_card_and_summary_show_risk(self):
        def make_limit_payload(code, volume_ratio):
            payload = render_payload(
                [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 132],
                None,
                price=132,
                change=9.8,
            )
            payload["stock_code"] = code
            payload["structure_score"] = 4
            payload["volume_ratio"] = volume_ratio
            payload["result"].update({
                "decision": "WAIT",
                "action": 0,
                "price_behavior": "LIMIT_LOCK",
                "heat_state": "EXTREME",
                "trade_state": "AVOID",
                "rr": 1.8,
                "market_grade": "A",
                "entry_quality": "A",
            })
            return payload

        messages = generator.formatTelegramMessages(
            {
                "群創": make_limit_payload("3481", 0.62),
                "緯創": make_limit_payload("3231", 1.71),
            },
            "FULL DETAIL",
            None,
            None,
            {"market_theme_evidence": {"theme_status": "absent", "level": "absent"}},
            datetime(2026, 5, 29),
            report_phase="盤中",
        )

        summary = summary_message(messages)
        unheld = unheld_message(messages)
        low_volume_card = "【群創 3481】" + unheld.split("【群創 3481】", 1)[1].split("\n\n", 1)[0]
        attack_volume_card = "【緯創 3231】" + unheld.split("【緯創 3231】", 1)[1].split("\n\n", 1)[0]

        self.assertIn("【群創 3481】⏳ 等回測｜漲停不追", low_volume_card)
        self.assertIn("數據：RR -（過熱）｜綜合 49｜技術 49｜證據：過熱不適用｜V 0.62x", low_volume_card)
        self.assertIn("V 0.62x", low_volume_card)
        self.assertIn("買點：不買，等回測", low_volume_card)
        self.assertIn("【緯創 3231】⏳ 等回測｜漲停不追", attack_volume_card)
        self.assertIn("V 1.71x", attack_volume_card)
        self.assertNotIn("縮量漲停", attack_volume_card)
        self.assertNotIn("強勢準備：", summary)
        self.assertIn("未持倉 2｜可買 0｜不可追高觀察 0（不可買）｜僅追蹤 2（等回測）｜淘汰 0", summary)
        self.assertIn("僅追蹤 2（等回測）", summary)
        self.assertNotIn("群創｜可買", summary + unheld)
        self.assertNotIn("緯創｜可買", summary + unheld)

    def test_v20_2_4_r3_hot_prepare_overflow_counts_hidden_statuses(self):
        def make_payload(code, price, change, overrides):
            payload = render_payload(
                [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, price],
                None,
                price=price,
                change=change,
            )
            payload["stock_code"] = code
            payload["result"].update({
                "decision": "WAIT",
                "action": 0,
                "price_behavior": "NORMAL",
                "heat_state": "NORMAL",
                "trade_state": "WAIT",
                "rr": 1.5,
                "market_grade": "A",
                "entry_quality": "A",
            })
            payload["result"].update(overrides)
            return payload

        messages = generator.formatTelegramMessages(
            {
                "A": make_payload("0001", 132, 9.8, {
                    "price_behavior": "LIMIT_LOCK",
                    "heat_state": "EXTREME",
                    "trade_state": "AVOID",
                }),
                "B": make_payload("0002", 128, 6.1, {
                    "heat_state": "HOT",
                    "trade_state": "EXTENDED",
                }),
                "C": make_payload("0003", 121, 2.0, {
                    "structure_phase": "BREAKOUT_NEAR",
                    "breakout_distance": 2,
                }),
                "D": make_payload("0004", 127, 5.7, {
                    "heat_state": "HOT",
                    "trade_state": "EXTENDED",
                }),
                "E": make_payload("0005", 122, 2.1, {
                    "heat_state": "HOT",
                    "trade_state": "EXTENDED",
                }),
                "F": make_payload("0006", 123, 2.4, {
                    "structure_phase": "BREAKOUT_NEAR",
                    "breakout_distance": 3,
                }),
                "G": make_payload("0007", 120, 1.1, {
                    "trade_state": "LATE_ENTRY",
                    "rr": 0.8,
                    "market_grade": "B",
                }),
                "H": make_payload("0008", 108, -4.1, {
                    "decision": "FAIL",
                    "structure_phase": "FAILED_BREAKOUT",
                    "rr": 0.7,
                }),
            },
            "FULL DETAIL",
            None,
            None,
            {"market_theme_evidence": {"theme_status": "absent", "level": "absent"}},
            datetime(2026, 5, 29),
            report_phase="盤中",
        )

        summary = summary_message(messages)
        unheld = unheld_message(messages)

        self.assertIn("【05/29 盤中｜v20.4.47】", summary)
        self.assertIn("市場：進攻偏熱 R3｜執行動作 0｜今日新建倉 0｜持倉風控 0｜未持倉 8（僅追蹤5/淘汰1）", summary)
        self.assertNotIn("市場/結論：進攻偏熱｜R3；R3 進攻偏熱", summary)
        self.assertIn(
            "強勢準備：\n"
            "- 突破回測：C 待觸發，不追高\n"
            "- 突破回測：F 待觸發，不追高",
            summary,
        )
        strong_prepare_section = summary.split("強勢準備：", 1)[1].split("\n\n", 1)[0]
        self.assertEqual(strong_prepare_section.count("\n- "), 2)
        self.assertNotIn("同狀態", strong_prepare_section)
        self.assertNotIn("A 不可追高", strong_prepare_section)
        self.assertNotIn("B 不可買", strong_prepare_section)
        self.assertNotIn("D 不可買", strong_prepare_section)
        self.assertNotIn("E 不可買", strong_prepare_section)
        self.assertIn("未持倉 8｜可買 0｜不可追高觀察 2（不可買）｜僅追蹤 5（等冷卻3/等回測1/等RR修復1）｜淘汰 1", summary)
        for name, code, action, label in [
            ("A", "0001", "等回測", "漲停不追"),
            ("B", "0002", "等冷卻", "過熱觀察"),
            ("C", "0003", "不可追高觀察", "突破回測"),
            ("D", "0004", "等冷卻", "過熱觀察"),
            ("E", "0005", "等冷卻", "過熱觀察"),
            ("F", "0006", "不可追高觀察", "突破回測"),
        ]:
            icon = "⏳" if action in ["等冷卻", "等回測"] else "👀"
            self.assertIn(f"【{name} {code}】{icon} {action}｜{label}", unheld)
        self.assertIn("【G 0007】👀 等RR修復｜RR不足", unheld)
        self.assertIn("【H 0008】⛔ 淘汰｜突破失敗", unheld)
        self.assertNotIn("A｜可買", summary + unheld)
        self.assertNotIn("B｜可買", summary + unheld)
        self.assertNotIn("C｜可買", summary + unheld)
        self.assertNotIn("D｜可買", summary + unheld)
        self.assertNotIn("E｜可買", summary + unheld)
        self.assertNotIn("F｜可買", summary + unheld)

    def test_intraday_mobile_a1_unheld_non_actionable_not_primary_prepare(self):
        def make_payload(code, overrides):
            payload = render_payload(
                [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 132],
                None,
                price=132,
                change=6.2,
            )
            payload["stock_code"] = code
            payload["result"].update({
                "decision": "WAIT",
                "action": 0,
                "price_behavior": "NORMAL",
                "heat_state": "NORMAL",
                "trade_state": "WAIT",
                "market_grade": "A",
                "entry_quality": "A",
                "rr": 1.6,
                **overrides,
            })
            return payload

        messages = generator.formatTelegramMessages(
            {
                "台達電": make_payload("2308", {
                    "heat_state": "HOT",
                    "trade_state": "EXTENDED",
                }),
                "台積電": make_payload("2330", {
                    "price_behavior": "LIMIT_LOCK",
                    "heat_state": "EXTREME",
                    "trade_state": "AVOID",
                }),
            },
            "FULL DETAIL",
            None,
            None,
            {"market_theme_evidence": {"theme_status": "absent", "level": "absent"}},
            datetime(2026, 6, 2),
            report_phase="盤中",
        )

        summary = summary_message(messages)
        unheld = unheld_message(messages)
        hot_card = card_block(unheld, "【台達電 2308】")
        limit_card = card_block(unheld, "【台積電 2330】")

        self.assertIn("新倉：無有效進場", summary)
        self.assertIn("不可追高觀察 0（不可買）｜僅追蹤 2", summary)
        self.assertIn("【台達電 2308】⏳ 等冷卻｜過熱觀察", hot_card)
        self.assertIn("【台積電 2330】⏳ 等回測｜漲停不追", limit_card)
        for card in [hot_card, limit_card]:
            title_line = card.splitlines()[0]
            self.assertNotIn("可準備", title_line)
            self.assertNotIn("可買", title_line)
            self.assertNotIn("推薦", title_line)

    def test_intraday_mobile_a2_holding_primary_action_consistent(self):
        holding_payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 120],
            {"shares": 30, "avg_price": 100},
            price=120,
            change=1.2,
        )
        holding_payload["stock_code"] = "2376"
        holding_payload["holding_decision"] = {
            "action": "續抱",
            "level": "HOLD",
            "note": "買點未成立，暫不加碼",
            "warning_price": 112,
            "hard_stop_price": 105,
        }

        messages = generator.formatTelegramMessages(
            {"技嘉": holding_payload},
            "FULL DETAIL",
            None,
            None,
            {"market_theme_evidence": {"theme_status": "absent", "level": "absent"}},
            datetime(2026, 6, 2),
            report_phase="盤中",
        )

        summary = summary_message(messages)
        position = position_message(messages)
        card = card_block(position, "【技嘉 2376】")
        card_title_action = card.splitlines()[0].split("📌 ", 1)[1].split("｜", 1)[0]
        decision_action = first_line_for_prefix(card, "決策：").split("決策：", 1)[1].split("，", 1)[0].split("｜", 1)[0]
        control_line = first_line_for_prefix(summary, "1. 技嘉｜")
        control_action = control_line.split("｜")[2]

        self.assertEqual(card_title_action, "續抱觀察")
        self.assertEqual(decision_action, card_title_action)
        self.assertEqual(control_action, card_title_action)
        self.assertIn("決策：續抱觀察，買點未成立，暫不加碼", card)

    def test_intraday_mobile_a3_holding_order_matches_cards_control_and_index(self):
        def make_holding(code, price, avg_price, action, level):
            payload = render_payload(
                [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, price],
                {"shares": 20, "avg_price": avg_price},
                price=price,
                change=0.5,
            )
            payload["stock_code"] = code
            payload["holding_decision"] = {
                "action": action,
                "level": level,
                "note": "按風控處理",
                "warning_price": avg_price * 0.95,
                "hard_stop_price": avg_price * 0.9,
            }
            return payload

        messages = generator.formatTelegramMessages(
            {
                "技嘉": make_holding("2376", 120, 100, "續抱", "HOLD"),
                "英業達": make_holding("2356", 130, 100, "核心續抱", "HOLD_CORE"),
                "緯創": make_holding("3231", 122, 100, "續抱", "HOLD"),
                "南亞科": make_holding("2408", 118, 100, "續抱", "HOLD"),
                "智原": make_holding("3035", 116, 100, "續抱", "HOLD"),
                "建準": make_holding("2421", 114, 100, "續抱", "HOLD"),
            },
            "FULL DETAIL",
            None,
            None,
            {"market_theme_evidence": {"theme_status": "absent", "level": "absent"}},
            datetime(2026, 6, 2),
            report_phase="盤中",
        )

        summary = summary_message(messages)
        position = position_message(messages)
        card_order = [
            line.split("】", 1)[0].lstrip("【").split(" ", 1)[0]
            for line in position.splitlines()
            if line.startswith("【") and "】📌" in line
        ]
        control_section = summary.split("持倉風控檢查\n", 1)[1].split("\n\n", 1)[0]
        control_order = [
            line.split(". ", 1)[1].split("｜", 1)[0]
            for line in control_section.splitlines()
            if ". " in line
        ]
        index_line = first_line_for_prefix(summary, "📎 詳情索引：")
        index_order = index_line.split("持倉 ", 1)[1].split("｜", 1)[0].split("、")

        self.assertEqual(len(card_order), 6)
        self.assertEqual(len(control_order), 6)
        self.assertIn("6. ", control_section)
        self.assertNotIn("另有", control_section)
        self.assertNotIn("見詳情", control_section)
        self.assertEqual(control_order, card_order)
        self.assertEqual(index_order, card_order)

    def test_v20_2_5_post_market_noise_contract_with_prepare_only_tracking(self):
        holding_payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 130],
            {"shares": 313, "avg_price": 100, "realized_profit_taken_ratio": 0.25},
            price=130,
            change=5.2,
        )
        holding_payload["stock_code"] = "2356"
        holding_payload["position_events"] = {
            "event_count": 1,
            "sold_shares": 187,
            "sell_pct": 25,
            "shares_before": 500,
        }

        def make_watch(code, price, change, overrides):
            payload = render_payload(
                [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, price],
                None,
                price=price,
                change=change,
            )
            payload["stock_code"] = code
            payload["result"].update({
                "decision": "WAIT",
                "action": 0,
                "price_behavior": "NORMAL",
                "heat_state": "HOT",
                "trade_state": "EXTENDED",
                "rr": 1.5,
                "market_grade": "A",
                "entry_quality": "A",
            })
            payload["result"].update(overrides)
            return payload

        results = {"英業達": holding_payload}
        for index in range(1, 9):
            results[f"準備{index}"] = make_watch(f"10{index:02d}", 126 + index, 5 + index / 10, {})
        for index in range(1, 3):
            results[f"淘汰{index}"] = make_watch(f"20{index:02d}", 108 - index, -4 - index / 10, {
                "decision": "FAIL",
                "structure_phase": "FAILED_BREAKOUT",
                "heat_state": "NORMAL",
                "trade_state": "WAIT",
                "rr": 0.7,
            })

        messages = generator.formatTelegramMessages(
            results,
            "FULL DETAIL",
            None,
            None,
            {"market_theme_evidence": {"theme_status": "absent", "level": "absent"}},
            datetime(2026, 5, 29),
            report_phase="盤後",
        )

        summary = summary_message(messages)

        self.assertIn("【05/29 盤後｜v20.4.47】", summary)
        self.assertIn("📌 盤後簡報", summary)
        self.assertIn("結論：今日無有效新倉；既有持倉以收盤後風控觀察為主。", summary)
        self.assertIn("明日前確認：觀察持倉是否跌破警戒；未持倉標的重新等待有效進場。", summary)
        self.assertNotIn("今日交易紀錄：無新增", summary)
        self.assertNotIn("今日交易紀錄\n無新增", summary)
        self.assertNotIn("其中僅追蹤 0 檔拆分", summary)
        self.assertNotIn("等冷卻 0", summary)
        self.assertNotIn("等回測 0", summary)
        self.assertNotIn("等RR修復 0", summary)
        self.assertNotIn("等量能 0", summary)
        self.assertNotIn("非執行追蹤合計 8", summary)
        self.assertNotIn("未持倉追蹤 8", summary)

    def test_intraday_v20_0_13_legacy_market_summary_cannot_confirm_theme(self):
        hot_payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 132],
            None,
            price=132,
            change=6.4,
        )
        hot_payload["stock_code"] = "1216"
        hot_payload["result"].update({
            "decision": "WAIT",
            "action": 0,
            "breakout_distance": 1,
            "price_behavior": "NORMAL",
            "heat_state": "HOT",
            "trade_state": "EXTENDED",
            "rr": 1.4,
            "market_grade": "A",
        })

        with patch.object(generator, "get_market_phase", return_value="盤中"):
            messages = generator.formatTelegramMessages(
                {"食品甲": hot_payload},
                "FULL DETAIL",
                None,
                None,
                "AI / 電子供應鏈仍偏多",
                datetime(2026, 5, 28),
            )

        summary = summary_message(messages)

        self.assertIn("【05/28 盤中｜v20.4.47】", summary)
        self.assertIn("🧭 主線：市場偏多但買點未成立。", summary)
        self.assertIn("新倉：無有效進場", summary)
        self.assertIn("買點未成立", summary)
        self.assertNotIn("AI / 電子供應鏈仍偏多", summary)
        self.assertNotIn("AI 題材偏多", summary)
        self.assertNotIn("電子供應鏈偏多", summary)

    def test_intraday_holding_control_keeps_next_day_text_in_next_day_plan(self):
        payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 122],
            {"shares": 100, "avg_price": 110},
            price=122,
            change=2.1,
        )
        payload["stock_code"] = "2376"
        payload["holding_decision"] = {
            "action": "加碼 20%",
            "level": "ADD_20",
            "note": "趨勢延續",
            "warning_price": 115,
            "hard_stop_price": 108,
            "allow_add": True,
        }
        payload["position_events"] = {"event_count": 1, "bought_shares": 100}
        payload["today_action"] = "BUY"

        with patch.object(generator, "get_market_phase", return_value="盤中"):
            messages = generator.formatTelegramMessages(
                {"技嘉": payload},
                "FULL DETAIL",
                None,
                None,
                "⏳ 觀望",
                datetime(2026, 5, 28),
            )

        summary = summary_message(messages)
        self.assertIn("持倉風控檢查\n1. 技嘉｜+10.91%｜新倉風控觀察｜盤中觀察修復狀況", summary)
        self.assertNotIn("持倉風控檢查\n1. 技嘉｜+10.91%｜新倉風控觀察｜明日未修復降級", summary)
        self.assertNotIn("隔日計畫", summary)
        self.assertNotIn("盤中觀察修復：技嘉收盤未修復則列入隔日降級檢查", summary)
        self.assertNotIn("明日未修復", summary)
        self.assertNotIn("隔日未修復", summary)

    def test_v20_0_14_message_list_uses_single_report_phase_when_phase_drifts(self):
        payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119],
            None,
            price=119,
            change=2.1,
        )
        payload["stock_code"] = "2301"
        payload["result"].update({
            "decision": "BUY",
            "action": 0.1,
            "entry_quality": "A",
            "heat_state": "NORMAL",
            "trade_state": "READY",
            "rr": 1.8,
            "market_grade": "A",
        })
        payload["backtest_context"] = {
            "sample": 36,
            "win_rate": 58,
            "avg_return": 1.2,
        }

        with patch.object(generator, "get_market_phase", side_effect=["盤中", "盤後"]) as phase_mock:
            messages = generator.formatTelegramMessages(
                {"光寶科": payload},
                "FULL DETAIL",
                "光寶科",
                88,
                "🟡 局部機會",
                datetime(2026, 5, 28),
                strategy_evidence_summary=AVAILABLE_STRATEGY_EVIDENCE,
            )

        summary = summary_message(messages)
        unheld = unheld_message(messages)

        self.assertEqual(phase_mock.call_count, 1)
        self.assertIn("【05/28 盤中｜v20.4.47】", summary)
        self.assertIn("市場：中性觀察 R2｜執行動作 0｜新倉建議 1｜今日新建倉 0", summary)
        self.assertNotIn("✅ 今日盤中交易執行\n光寶科 可買（分批，不追價）", summary)
        self.assertIn("新倉建議\n光寶科 可買（分批，不追價）｜尚未買入｜建議分批｜盤中觸發", summary)
        self.assertIn("原因：持倉無需處理，新倉僅列可行動候選。", summary)
        self.assertIn("風險：新倉：尚未買入，不列入交易執行，分批且不追價", summary)
        self.assertIn("【光寶科 2301】🟢 可買｜10%倉｜買點成立", unheld)
        self.assertIn("盤中觸發：", unheld)
        self.assertIn("📎 詳情索引：持倉 無｜新倉建議 1", summary)
        self.assertNotIn("明日計畫 1", summary)
        self.assertNotIn("明日追蹤｜10%倉", unheld)

    def test_v20_0_14_post_market_fixture_uses_next_day_plan_semantics(self):
        payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119],
            None,
            price=119,
            change=2.1,
        )
        payload["stock_code"] = "2301"
        payload["result"].update({
            "decision": "BUY",
            "action": 0.1,
            "entry_quality": "A",
            "heat_state": "NORMAL",
            "trade_state": "READY",
            "rr": 1.8,
            "market_grade": "A",
        })
        payload["backtest_context"] = {
            "sample": 36,
            "win_rate": 58,
            "avg_return": 1.2,
        }

        with patch.object(generator, "get_market_phase", return_value="盤後"):
            messages = generator.formatTelegramMessages(
                {"光寶科": payload},
                "FULL DETAIL",
                "光寶科",
                88,
                "🟡 局部機會",
                datetime(2026, 5, 28),
                strategy_evidence_summary=AVAILABLE_STRATEGY_EVIDENCE,
            )

        summary = summary_message(messages)
        unheld = unheld_message(messages)

        self.assertIn("【05/28 盤後｜v20.4.47】", summary)
        self.assertIn("📌 盤後簡報", summary)
        self.assertIn("新倉：無有效進場", summary)
        self.assertIn("可準備：1 檔需明日開盤後確認，未確認前不可下單", summary)
        self.assertIn("市場：中性觀察 R2｜執行動作 0｜今日新建倉 0｜持倉風控 0｜未持倉 1（可準備1/僅追蹤0/淘汰0）", summary)
        self.assertIn("未持倉 1｜可準備 1（不可買）", summary)
        self.assertNotIn("新倉建議\n光寶科 可買（分批，不追價）", summary)
        self.assertNotIn("新增有效進場 1", summary)
        self.assertNotIn("光寶科 可買（分批，不追價）", summary)
        self.assertIn("【光寶科 2301】🟡 明日準備｜不可買｜開盤後確認", unheld)
        self.assertIn("買點：明日準備｜不可下單", unheld)
        self.assertIn("卡關主因：開盤確認未完成", unheld)
        self.assertIn("量化差距：盤後待開盤確認", unheld)
        self.assertIn("解鎖：明日開盤後仍守突破區 / 不追價", unheld)
        self.assertIn("原因：盤後待確認，需開盤後重新確認", unheld)
        self.assertNotIn("既有買點與倉位規則通過", unheld)
        self.assertNotIn("證據：資料不足", unheld)
        self.assertIn("明日觸發：", unheld)
        self.assertIn("RR 1.8", unheld)
        self.assertIn("突破確認", unheld)
        self.assertIn("回測（光寶科）：", summary)
        self.assertIn("回測（光寶科）：樣本36｜參考度高｜3日勝率58%｜相對+1.2%｜略優；回測僅輔助，分批小倉、不追價", unheld)
        self.assertNotIn("✅ 今日盤中交易執行", summary)
        self.assertNotIn("明日計畫 1", summary)
        self.assertNotIn("存在合格買點，分批執行", summary)
        self.assertNotIn("【光寶科 2301】🟢 可買｜10%倉", unheld)
        self.assertNotIn("明日追蹤｜10%倉", unheld)
        self.assertNotIn("買點成立", unheld)
        self.assertNotIn("買點：可買｜建議 10%倉", unheld)

    def test_v20_4_39_post_market_mixed_trend_and_prepare_keeps_trend_actionable(self):
        ordinary_payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119],
            None,
            price=119,
            change=2.1,
        )
        ordinary_payload["stock_code"] = "2301"
        ordinary_payload["result"].update({
            "decision": "BUY",
            "action": 0.1,
            "entry_quality": "A",
            "heat_state": "NORMAL",
            "trade_state": "READY",
            "rr": 1.8,
            "market_grade": "A",
        })
        ordinary_payload["backtest_context"] = {
            "sample": 36,
            "win_rate": 58,
            "avg_return": 1.2,
        }
        trend_payload = trend_continuation_payload()

        with patch.object(generator, "get_market_phase", return_value="盤後"):
            messages = generator.formatTelegramMessages(
                {"智原": trend_payload, "光寶科": ordinary_payload},
                "FULL DETAIL",
                "智原",
                90,
                "市場偏強",
                datetime(2026, 6, 3, 16, 0),
                strategy_evidence_summary=AVAILABLE_STRATEGY_EVIDENCE,
            )

        summary = summary_message(messages)
        unheld = unheld_message(messages)
        trend_card = card_block(unheld, "【智原 3231】")
        ordinary_card = card_block(unheld, "【光寶科 2301】")

        self.assertIn("【06/03 盤後｜v20.4.47】", summary)
        self.assertIn("趨勢延續買入 1 檔小倉", summary)
        self.assertIn("新增有效進場：1 檔需明日開盤前確認", summary)
        self.assertIn("可準備：1 檔需明日開盤後確認，未確認前不可下單", summary)
        self.assertIn("未持倉 2｜趨勢延續 1｜可準備 1（不可買）", summary)
        self.assertIn("智原 趨勢延續買入（小倉<=15%）｜尚未買入｜回踩低點下方停損｜明日開盤後確認", summary)
        self.assertNotIn("新倉：無有效進場", summary)
        self.assertNotIn("新增有效進場：無", summary)
        self.assertNotIn("光寶科 可買（分批，不追價）", summary)

        self.assertIn("【智原 3231】🟢 趨勢延續買入｜小倉", trend_card)
        self.assertIn("買點：趨勢延續買入｜小倉 <=15%｜回測 55% 勝 / +2.26%", trend_card)
        self.assertIn("【光寶科 2301】🟡 明日準備｜不可買｜開盤後確認", ordinary_card)
        self.assertIn("買點：明日準備｜不可下單", ordinary_card)
        self.assertIn("卡關主因：開盤確認未完成", ordinary_card)
        self.assertIn("量化差距：盤後待開盤確認", ordinary_card)
        self.assertIn("解鎖：明日開盤後仍守突破區 / 不追價", ordinary_card)
        self.assertIn("原因：盤後待確認，需開盤後重新確認", ordinary_card)
        self.assertNotIn("證據：資料不足", ordinary_card)
        self.assertIn("回測（光寶科）：樣本36｜參考度高｜3日勝率58%｜相對+1.2%｜略優；回測僅輔助，分批小倉、不追價", ordinary_card)
        self.assertNotIn("明日追蹤｜10%倉", ordinary_card)
        self.assertNotIn("買點成立", ordinary_card)

    def test_telegram_messages_can_include_detail_when_requested(self):
        payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119],
            None,
            price=119,
            change=1.4,
        )
        generator.render_stock("建準", payload)
        messages = generator.formatTelegramMessages(
            {"建準": payload},
            "FULL DETAIL",
            None,
            None,
            "⏳ 觀望",
            datetime(2026, 5, 25),
            include_detail=True,
        )

        self.assertIn("【完整詳情備份】", detail_message(messages))
        self.assertIn("FULL DETAIL", detail_message(messages))
        self.assertIn("【持倉標的】", position_message(messages))
        self.assertIn("【未持倉標的】", unheld_message(messages))
        self.assertIn("｜v20.4.47】", summary_message(messages))
        self.assertIs(messages[0], position_message(messages))
        self.assertIs(messages[1], unheld_message(messages))
        self.assertIs(messages[2], summary_message(messages))
        self.assertIs(messages[2], evidence_message(messages))
        self.assertIs(messages[-1], detail_message(messages))

    def test_v20_4_12_complete_message_list_orders_holdings_unheld_summary_evidence_details(self):
        holding_payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119],
            {"shares": 50, "avg_price": 118},
            price=119,
            change=1.4,
        )
        holding_payload["holding_decision"] = {
            "action": "續抱",
            "level": "HOLD",
            "warning_price": 113,
            "hard_stop_price": 109,
        }
        watch_payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119],
            None,
            price=119,
            change=1.4,
        )
        watch_payload["stock_code"] = "2421"
        watch_payload["result"]["rr"] = 0.5
        watch_payload["result"]["trade_state"] = "LATE_ENTRY"

        messages = generator.formatTelegramMessages(
            {"智原": holding_payload, "建準": watch_payload},
            "raw_source_table: verbose row\nbacktest debug line",
            None,
            None,
            {"trade_date": "2026-06-01"},
            datetime(2026, 6, 1),
            include_detail=True,
            report_phase="盤中",
        )

        self.assertEqual(len(messages), 4)
        self.assertIs(messages[0], position_message(messages))
        self.assertIs(messages[1], unheld_message(messages))
        self.assertIs(messages[2], summary_message(messages))
        self.assertIs(messages[2], evidence_message(messages))
        self.assertIn("【持倉標的】", messages[0])
        self.assertIn("【未持倉標的】", messages[1])
        self.assertTrue(messages[3].startswith("【Details Backup】"))
        self.assertIn("【06/01 盤中｜v20.4.47】", messages[0])
        self.assertIn("【06/01 盤中｜v20.4.47】", messages[1])
        self.assertIn("【06/01 盤中｜v20.4.47】", messages[2])
        self.assertNotIn("v20.4.11", "\n\n".join(messages))
        self.assertIn("智原", messages[0])
        self.assertIn("續抱", messages[0])
        self.assertIn("建準", messages[1])
        self.assertNotIn("智原", messages[1])
        self.assertNotIn("建準", messages[0])
        self.assertIn("🧾 v20.4.47 簡報", messages[2])
        self.assertEqual(messages[2].count("\n決策簡報\n"), 1)
        self.assertNotIn("\n資料依據\n", messages[2])
        self.assertIn("持倉：依第一則既有卡片處理，不新增第二個主行動。", messages[2])
        self.assertIn("新倉：無有效進場", messages[2])
        self.assertNotIn("策略樣本：缺少可驗證來源，本次不納入買賣判斷。", messages[2])
        for term in FORBIDDEN_SHORT_EVIDENCE_TERMS:
            self.assertNotIn(term, messages[2])

    def test_v20_4_12_2356_still_holding_without_confirmed_second_tp_fails_closed(self):
        payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 130],
            {"shares": 225, "avg_price": 100, "realized_profit_taken_ratio": 0.5},
            price=130,
            change=5.2,
        )
        payload["stock_code"] = "2356"
        payload["holding_decision"] = {
            "action": "停利 25%",
            "level": "TAKE_PROFIT_25",
            "shares": 56,
            "note": "過熱延伸再次達停利條件",
            "warning_price": 123,
            "hard_stop_price": 118,
            "allow_add": False,
        }
        payload["cross_day_context"] = {
            "source_status": "ready",
            "source_of_truth": ["positions", "position_events"],
            "previous_action": "take_profit",
            "previous_action_date": "2026-05-29",
            "dedupe_guard": "prior_take_profit_completed",
            "execution_memory": {
                "source": "position_events",
                "latest_trade_date": "2026-05-29",
                "sell_deltas": [-112],
                "sold_shares": 112,
                "labels": ["停利 25%"],
            },
        }

        messages = generator.formatTelegramMessages(
            {"英業達": payload},
            "FULL DETAIL",
            None,
            None,
            {"trade_date": "2026-06-01"},
            datetime(2026, 6, 1),
            report_phase="盤中",
        )

        rendered = "\n\n".join(messages)
        self.assertEqual(generator.position_summary_action("英業達", payload), "停利記憶不足")
        self.assertIn("持倉：英業達 先補交易執行記憶", evidence_message(messages))
        self.assertNotIn("資料依據", evidence_message(messages))
        self.assertNotIn("資料依據", evidence_message(messages))
        for term in FORBIDDEN_SHORT_EVIDENCE_TERMS:
            self.assertNotIn(term, evidence_message(messages))
        self.assertIn("停利記憶不足", rendered)
        self.assertNotIn("第二段已執行", rendered)
        self.assertNotIn("已賣出 -112", rendered)
        self.assertNotIn("英業達｜已執行", rendered)
        self.assertNotIn("本次建議 56 股", rendered)

    def test_v20_4_13_noise_reduction_moves_verbose_detail_after_short_evidence(self):
        payload = {
            "stock_code": "2421",
            "price": 100,
            "change": 0,
            "price_source": "runtime-cache",
            "daily_source": "runtime-cache",
            "result": {
                "decision": "BUY",
                "action": 0.1,
                "rr": 1.8,
                "heat_state": "NORMAL",
                "trade_state": "READY",
                "structure_phase": "BREAKOUT_CONFIRM",
                "price_behavior": "NORMAL",
                "market_grade": "A",
                "volume_state": "STRONG",
                "volume_price_state": "EXPANSION",
                "structure_state": "STRONG",
                "entry_quality": "A",
                "confidence_score": 86,
            },
            "holding": None,
            "structure_score": 5,
            "volume_ratio": 1.4,
            "closes": [90, 91, 92],
            "volumes": [1000, 1100, 1200],
        }
        noisy_detail = "raw_source_table: price runtime-cache\nbacktest detail row: sample=3"

        messages = generator.formatTelegramMessages(
            {"建準": payload},
            noisy_detail,
            "建準",
            88,
            {"trade_date": "2026-06-01"},
            datetime(2026, 6, 1),
            include_detail=True,
            report_phase="盤中",
        )

        main_messages = "\n\n".join(messages[:-1])
        self.assertIn("新倉：無有效進場", summary_message(messages))
        self.assertNotIn("Source：核心價格 insufficient-data", summary_message(messages))
        self.assertNotIn("策略樣本本輪不採用", evidence_message(messages))
        self.assertNotIn("資料依據", evidence_message(messages))
        self.assertNotIn("資料依據", evidence_message(messages))
        for term in FORBIDDEN_SHORT_EVIDENCE_TERMS:
            self.assertNotIn(term, evidence_message(messages))
        self.assertNotIn("raw_source_table", main_messages)
        self.assertNotIn("backtest detail row", main_messages)
        self.assertIn(noisy_detail, detail_message(messages))

    def test_v20_4_13_unavailable_strategy_sample_short_evidence_fails_closed_naturally(self):
        payload = {
            "stock_code": "2421",
            "price": None,
            "change": None,
            "price_source": None,
            "daily_source": None,
            "result": {
                "decision": "BUY",
                "action": 0.1,
                "rr": 1.8,
                "heat_state": "NORMAL",
                "trade_state": "READY",
                "structure_phase": "BREAKOUT_CONFIRM",
                "price_behavior": "NORMAL",
                "market_grade": "A",
                "volume_state": "STRONG",
                "volume_price_state": "EXPANSION",
                "structure_state": "STRONG",
                "entry_quality": "A",
                "confidence_score": 86,
            },
            "holding": None,
            "structure_score": 5,
            "volume_ratio": 1.4,
            "closes": [],
            "volumes": [],
        }

        messages = generator.formatTelegramMessages(
            {"建準": payload},
            "FULL DETAIL",
            "建準",
            88,
            {"trade_date": "2026-06-01"},
            datetime(2026, 6, 1),
            strategy_evidence_summary=structured_strategy_evidence(
                "insufficient-data",
                row_count=0,
                rendered_text="📊 策略證據 v20.0\n狀態：不可用\n原因：樣本不足（有效樣本 0）",
            ),
            report_phase="盤中",
        )

        evidence = evidence_message(messages)
        rendered = "\n\n".join(messages)
        self.assertEqual(len(messages), 3)
        self.assertIs(messages[0], position_message(messages))
        self.assertIs(messages[1], unheld_message(messages))
        self.assertIs(messages[2], evidence)
        self.assertIn("新倉：無有效進場", evidence)
        self.assertNotIn("策略樣本本輪不採用", evidence)
        self.assertNotIn("樣本35", evidence)
        self.assertNotIn("策略樣本：樣本不足，本次不納入買賣判斷。", evidence)
        self.assertNotIn("📊 策略證據 v20.0", rendered)
        self.assertNotIn("可買｜建議", rendered)
        self.assertNotIn("建準｜可買", rendered)
        for term in FORBIDDEN_SHORT_EVIDENCE_TERMS:
            self.assertNotIn(term, evidence)

    def test_v20_4_20_holding_non_add_rr_shows_not_applicable(self):
        payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119],
            {"shares": 50, "avg_price": 118},
            price=119,
            change=1.4,
        )
        payload["result"]["rr"] = 2.73
        payload["holding_decision"] = {
            "action": "續抱",
            "level": "HOLD",
            "warning_price": 113,
            "hard_stop_price": 109,
            "allow_add": False,
        }

        messages = generator.formatTelegramMessages(
            {"智原": payload},
            "FULL DETAIL",
            None,
            None,
            {"trade_date": "2026-06-01"},
            datetime(2026, 6, 1),
            report_phase="盤中",
        )

        position = position_message(messages)
        self.assertIn("數據：不適用（既有持倉）", position)
        self.assertNotRegex(position, r"數據：RR 2\.73")
        self.assertEqual(payload["result"]["rr"], 2.73)

    def test_v20_4_21_afterhours_mobile_readability_probe(self):
        holding_payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119],
            {"shares": 50, "avg_price": 118},
            price=119,
            change=1.4,
        )
        holding_payload["stock_code"] = "3035"
        holding_payload["result"]["rr"] = 2.73
        holding_payload["holding_decision"] = {
            "action": "加碼 10%",
            "level": "ADD_10",
            "warning_price": 113,
            "hard_stop_price": 109,
            "allow_add": True,
        }
        holding_payload["position_events"] = {"bought_shares": 50, "action": "BUY"}
        candidate_payload = render_payload(
            [50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 70],
            None,
            price=70,
            change=2.0,
        )
        candidate_payload["stock_code"] = "2301"
        candidate_payload["result"].update({
            "decision": "BUY",
            "action": 0.1,
            "rr": 2.4,
            "trade_state": "READY",
            "market_grade": "A",
        })
        tracking_payload = render_payload(
            [80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99],
            None,
            price=99,
            change=0.8,
        )
        tracking_payload["stock_code"] = "2421"
        tracking_payload["result"].update({
            "decision": "WAIT",
            "action": 0,
            "rr": 1.2,
            "trade_state": "WATCH",
        })

        messages = generator.formatTelegramMessages(
            {
                "建準": holding_payload,
                "光寶科": candidate_payload,
                "觀察股": tracking_payload,
            },
            "FULL DETAIL",
            "光寶科",
            88,
            {"trade_date": "2026-06-01"},
            datetime(2026, 6, 1),
            strategy_evidence_summary=structured_strategy_evidence(
                "insufficient-data",
                row_count=3,
                rendered_text="📊 策略證據 v20.0\n狀態：不可用\n原因：樣本不足（有效樣本 3）",
            ),
            report_phase="盤後",
        )

        position = position_message(messages)
        unheld = unheld_message(messages)
        brief = evidence_message(messages)
        rendered = "\n\n".join(messages)

        self.assertIn("📌 盤後簡報", brief)
        self.assertNotIn("今日交易\n新增交易建議：無", brief)
        self.assertIn("持倉風控檢查\n1. 建準", brief)
        self.assertIn("未持倉漏斗（非執行）：", brief)
        self.assertEqual(rendered.count("策略樣本：樣本不足，本次不納入買賣判斷。"), 0)
        self.assertNotIn("策略樣本：不可用，本次不納入判斷", position)
        self.assertNotIn("策略樣本：不可用，本次不納入判斷", unheld)
        self.assertNotIn("missing-source", brief)
        self.assertNotIn("盤中留意", rendered)
        self.assertNotIn("盤中觸發", rendered)
        self.assertNotIn("即時進場", rendered)
        self.assertNotIn("盤中先觀察", rendered)
        self.assertNotIn("盤中觀察修復狀況", rendered)
        self.assertIn("下一步：明日觀察是否守住警戒，未修復再降級", position)
        self.assertIn("新倉風控觀察，暫不加碼", position)
        self.assertIn("數據：不適用（既有持倉）", position)
        self.assertNotRegex(position, r"數據：RR 2\.73")
        self.assertIn("數據：RR -（過熱）", unheld)
        self.assertNotIn("資料：現價與 OHLCV 已確認；RR/分數/量能為模型推算", unheld)
        self.assertNotIn("資料依據", brief)
        self.assertIn("未持倉 2｜可買 0｜不可追高觀察 1（不可買）｜僅追蹤 1（等冷卻）｜淘汰 0", brief)
        self.assertNotIn("資料依據", brief)
        self.assertNotIn("交易證據日", rendered)
        self.assertNotIn("策略勝率", rendered)
        self.assertNotIn("勝率證據", rendered)

    def test_v20_4_24_weak_far_holding_shows_observation_days(self):
        holding_payload = render_payload(
            [300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311, 312, 313, 314, 315, 316, 317, 318, 309],
            {"shares": 30, "avg_price": 310, "observation_days": 2},
            price=309,
            change=-0.3,
        )
        holding_payload["stock_code"] = "3035"
        holding_payload["result"].update({
            "structure_phase": "WEAK",
            "volume_state": "WEAK",
            "breakout_distance": 4.07,
        })
        holding_payload["holding_decision"] = {
            "action": "續抱觀察",
            "level": "HOLD_WATCH",
            "note": "轉弱觀察，不加碼",
            "warning_price": 294.5,
            "hard_stop_price": 285.2,
        }

        messages = generator.formatTelegramMessages(
            {"智原": holding_payload},
            "FULL DETAIL",
            None,
            None,
            {"trade_date": "2026-06-01"},
            datetime(2026, 6, 1),
            report_phase="盤中",
        )

        position = position_message(messages)
        rendered = "\n\n".join(messages)

        self.assertIn("【智原 3035】📌 續抱觀察", position)
        self.assertIn("條件：弱勢觀察第 2 天；若第 3 天仍未重新接近買點 / 突破區，降低優先級", position)
        self.assertNotIn("條件：觀察：弱勢觀察", position)
        self.assertEqual(rendered.count("弱勢觀察第 2 天"), 1)
        self.assertNotIn("建議賣出", rendered)
        self.assertNotIn("已降級", rendered)

    def test_v20_4_24_weak_far_holding_shows_position_events_observation_days(self):
        holding_payload = render_payload(
            [300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311, 312, 313, 314, 315, 316, 317, 318, 309],
            {"shares": 30, "avg_price": 310},
            price=309,
            change=-0.3,
        )
        holding_payload["stock_code"] = "3035"
        holding_payload["position_events"] = {"event_count": 1, "observation_days": 3}
        holding_payload["result"].update({
            "structure_phase": "WEAK",
            "volume_state": "WEAK",
            "breakout_distance": 4.07,
        })
        holding_payload["holding_decision"] = {
            "action": "續抱觀察",
            "level": "HOLD_WATCH",
            "note": "轉弱觀察，不加碼",
            "warning_price": 294.5,
            "hard_stop_price": 285.2,
        }

        messages = generator.formatTelegramMessages(
            {"智原": holding_payload},
            "FULL DETAIL",
            None,
            None,
            {"trade_date": "2026-06-01"},
            datetime(2026, 6, 1),
            report_phase="盤中",
        )

        position = position_message(messages)
        rendered = "\n\n".join(messages)

        self.assertIn("條件：弱勢觀察第 3 天；若第 4 天仍未重新接近買點 / 突破區，降低優先級", position)
        self.assertNotIn("條件：觀察：弱勢觀察", position)
        self.assertEqual(rendered.count("弱勢觀察第 3 天"), 1)
        self.assertNotIn("已降級", rendered)

    def test_v20_4_24_weak_far_holding_observation_days_missing_fails_closed(self):
        holding_payload = render_payload(
            [300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311, 312, 313, 314, 315, 316, 317, 318, 309],
            {"shares": 30, "avg_price": 310, "observation_days": None},
            price=309,
            change=-0.3,
        )
        holding_payload["stock_code"] = "3035"
        holding_payload["observation_days"] = 2
        holding_payload["result"].update({
            "structure_phase": "WEAK",
            "volume_state": "WEAK",
            "breakout_distance": 4.07,
            "observation_days": 4,
        })
        holding_payload["holding_decision"] = {
            "action": "續抱觀察",
            "level": "HOLD_WATCH",
            "note": "轉弱觀察，不加碼",
            "warning_price": 294.5,
            "hard_stop_price": 285.2,
        }

        messages = generator.formatTelegramMessages(
            {"智原": holding_payload},
            "FULL DETAIL",
            None,
            None,
            {"trade_date": "2026-06-01"},
            datetime(2026, 6, 1),
            report_phase="盤中",
        )

        position = position_message(messages)
        rendered = "\n\n".join(messages)

        self.assertIn("【智原 3035】📌 續抱觀察", position)
        self.assertIn("條件：觀察天數未確認；若無法重新接近買點 / 突破區，降低優先級", position)
        self.assertNotIn("條件：觀察：觀察天數未確認", position)
        self.assertNotIn("弱勢觀察第 1 天", rendered)
        self.assertNotIn("弱勢觀察第 2 天", rendered)
        self.assertNotIn("弱勢觀察第 4 天", rendered)
        self.assertNotIn("已降級", rendered)
        self.assertNotIn("建議賣出", rendered)

    def test_v20_4_24_weak_far_holding_position_events_list_fails_closed_without_crash(self):
        holding_payload = render_payload(
            [300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311, 312, 313, 314, 315, 316, 317, 318, 309],
            {"shares": 30, "avg_price": 310},
            price=309,
            change=-0.3,
        )
        holding_payload["stock_code"] = "3035"
        holding_payload["position_events"] = [{"observation_days": 7}]
        holding_payload["result"].update({
            "structure_phase": "WEAK",
            "volume_state": "WEAK",
            "breakout_distance": 4.07,
        })
        holding_payload["holding_decision"] = {
            "action": "續抱觀察",
            "level": "HOLD_WATCH",
            "note": "轉弱觀察，不加碼",
            "warning_price": 294.5,
            "hard_stop_price": 285.2,
        }

        messages = generator.formatTelegramMessages(
            {"智原": holding_payload},
            "FULL DETAIL",
            None,
            None,
            {"trade_date": "2026-06-01"},
            datetime(2026, 6, 1),
            report_phase="盤中",
        )

        position = position_message(messages)
        rendered = "\n\n".join(messages)

        self.assertIn("【智原 3035】📌 續抱觀察", position)
        self.assertIn("條件：觀察天數未確認；若無法重新接近買點 / 突破區，降低優先級", position)
        self.assertNotIn("條件：觀察：觀察天數未確認", position)
        self.assertNotIn("弱勢觀察第 7 天", rendered)
        self.assertNotIn("已降級", rendered)
        self.assertNotIn("建議賣出", rendered)

    def test_v20_4_24_observation_days_only_trusts_persistent_sources(self):
        trusted_cases = [
            ({"holding": {"observation_days": 2}}, 2),
            ({"holding": {"watch_days": "3"}}, 3),
            ({"position_events": {"observation_days": 4}}, 4),
        ]
        for payload, expected in trusted_cases:
            with self.subTest(payload=payload):
                self.assertEqual(generator.positive_observation_days_from_holding(payload), expected)

        untrusted_or_invalid_cases = [
            {"observation_days": 2},
            {"watch_days": 2},
            {"result": {"observation_days": 2}},
            {"result": {"watch_days": 2}},
            {"holding": {"observation_days": None}},
            {"holding": {"observation_days": 0}},
            {"holding": {"observation_days": "2.5"}},
            {"holding": {"observation_days": 1.5}},
            {"holding": {"observation_days": True}},
            {"position_events": {"observation_days": 0}},
            {"position_events": {"watch_days": "pending"}},
            {"position_events": [{"watch_days": 5}]},
            {"position_events": [{"observation_days": 7}]},
        ]
        for payload in untrusted_or_invalid_cases:
            with self.subTest(payload=payload):
                self.assertIsNone(generator.positive_observation_days_from_holding(payload))

    def test_v20_4_20_strategy_sample_unavailable_card_hides_backtest_numbers(self):
        payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119],
            None,
            price=119,
            change=1.4,
        )
        payload["backtest_context"] = {
            "sample": 35,
            "win_rate": 71,
            "avg_return": 2.4,
        }

        messages = generator.formatTelegramMessages(
            {"建準": payload},
            "FULL DETAIL",
            "建準",
            88,
            {"trade_date": "2026-06-01"},
            datetime(2026, 6, 1),
            strategy_evidence_summary=structured_strategy_evidence(
                "insufficient-data",
                row_count=3,
                rendered_text="📊 策略證據 v20.0\n狀態：不可用\n原因：樣本不足（有效樣本 3）",
            ),
            report_phase="盤中",
        )

        unheld = unheld_message(messages)
        evidence = evidence_message(messages)
        self.assertNotIn("策略樣本：不可用，本次不納入判斷", unheld)
        self.assertNotIn("樣本35", unheld)
        self.assertNotIn("3日勝率71%", unheld)
        self.assertNotIn("相對+2.4%", unheld)
        self.assertNotIn("樣本35", evidence)
        self.assertNotIn("3日勝率71%", evidence)
        self.assertNotIn("相對+2.4%", evidence)
        self.assertNotIn("回測分組", evidence)

    def test_v20_4_10_complete_report_context_manifest_maps_visible_fields(self):
        holding_payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119],
            {"shares": 50, "avg_price": 118},
            price=119,
            change=1.4,
        )
        holding_payload["daily_source"] = "yahoo"
        holding_payload["volume_ratio"] = 1.8
        holding_payload["holding_decision"] = {
            "action": "續抱",
            "level": "HOLD",
            "warning_price": 113,
            "hard_stop_price": 109,
        }
        watch_payload = render_payload(
            [50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 70],
            None,
            price=70,
            change=2.0,
        )
        watch_payload["stock_code"] = "2421"
        watch_payload["daily_source"] = "yahoo"
        watch_payload["volume_ratio"] = 1.5
        watch_payload["result"]["rr"] = 0.6
        watch_payload["result"]["trade_state"] = "LATE_ENTRY"

        market_summary = {
            "trade_date": "2026-05-29",
            "as_of": "2026-05-31",
            "market_theme_evidence": {
                "status": "confirmed",
                "source_status": "ready",
                "theme_status": "confirmed",
                "level": "confirmed",
                "source_of_truth": "production_db",
                "as_of": "2026-05-29",
                "sources": [{
                    "source_family": "production_db",
                    "source_type": "watchlist_breadth",
                    "source_name": "market_theme_confirmed_evidence",
                    "as_of": "2026-05-29",
                    "freshness": "same_day",
                    "freshness_reason": "same_trade_date",
                    "level": "confirmed",
                    "supports_claims": ["AI 主線偏多"],
                    "limitations": [],
                }, {
                    "source_family": "production_db",
                    "source_type": "market_index",
                    "source_name": "market_theme_index_daily_bars",
                    "as_of": "2026-05-29",
                    "freshness": "same_day",
                    "freshness_reason": "same_trade_date",
                    "level": "confirmed",
                    "supports_claims": ["AI 主線偏多"],
                    "limitations": [],
                }],
                "evidence_trend": {"observed_days": 20, "recent_supporting_days": 5},
            },
        }
        strategy_summary = (
            "📊 策略證據 v20.0\n"
            "策略樣本 / 分類回測\n"
            "狀態：不可用\n"
            "原因：缺 classification backtest source-of-truth"
        )

        context = generator.build_report_context(
            {"智原": holding_payload, "建準": watch_payload},
            market_summary,
            datetime(2026, 5, 31),
            strategy_evidence_summary=strategy_summary,
            report_phase="盤中",
        )
        fields = {item["field_name"]: item for item in context["evidence_manifest"]}

        self.assertEqual(context["report_context"]["version"], "v20.4.47")
        self.assertEqual(context["report_context"]["trade_date"], "2026-05-29")
        for key in [
            "report.version",
            "report.trade_date",
            "evidence.market_theme",
            "evidence.strategy_sample",
            "stock.智原.position",
            "stock.智原.execution_memory",
            "stock.智原.price",
            "stock.智原.risk",
            "stock.建準.price",
            "stock.建準.rr",
            "funnel.unheld_counts",
            "tomorrow.plan",
        ]:
            self.assertIn(key, fields)
            self.assertIn(fields[key]["source_status"], {
                "available",
                "derived",
                "missing-source",
                "source-error",
                "insufficient-data",
                "not-applicable",
            })
            self.assertIn("fallback_rule", fields[key])
            self.assertIn("source_of_truth", fields[key])
            for required in ["layer", "target", "source", "status", "use", "limit", "conflict", "visible_refs"]:
                self.assertIn(required, fields[key])
                self.assertNotIn(fields[key][required], ["", [], None])

        self.assertEqual(fields["evidence.strategy_sample"]["source_status"], "missing-source")
        self.assertFalse(fields["evidence.strategy_sample"]["decision_eligible"])
        self.assertEqual(fields["evidence.market_theme"]["source_status"], "available")

        messages = generator.formatTelegramMessages(
            {"智原": holding_payload, "建準": watch_payload},
            "FULL DETAIL",
            None,
            None,
            market_summary,
            datetime(2026, 5, 31),
            strategy_evidence_summary=strategy_summary,
            report_phase="盤中",
        )

        self.assertIn("🧾 v20.4.47 簡報", summary_message(messages))
        self.assertNotIn("Source：核心價格 available；持倉 available；策略樣本 missing-source；market/theme available", summary_message(messages))
        self.assertNotIn("📊 策略證據 v20.0", summary_message(messages))
        self.assertNotIn("資料：持倉與現價已確認；風控由持倉成本/停損推算", position_message(messages))
        self.assertIn("數據：不適用（既有持倉）", position_message(messages))
        self.assertNotIn("Source：position available｜price available｜risk derived｜RR derived", position_message(messages))
        self.assertNotRegex(position_message(messages), r"數據：RR [0-9]")
        self.assertNotIn("資料：現價與 OHLCV 已確認；RR/分數/量能為模型推算", unheld_message(messages))
        self.assertNotIn("Source：price available｜OHLCV available｜RR derived｜score derived｜volume derived", unheld_message(messages))
        self.assertNotIn("Source：漏斗 count", summary_message(messages))
        self.assertNotIn("資料依據", evidence_message(messages))
        self.assertNotIn("策略樣本：缺少可驗證來源，本次不納入買賣判斷。", evidence_message(messages))
        for term in FORBIDDEN_SHORT_EVIDENCE_TERMS:
            self.assertNotIn(term, evidence_message(messages))
        self.assertNotRegex(evidence_message(messages), r"\d{4}-\d{2}-\d{2}T")

    def test_v20_4_18_structural_artifacts_cover_three_fail_closed_cases(self):
        for case in [
            "all_sources_available",
            "missing_strategy_sample_source",
            "ledger_position_conflict",
        ]:
            with self.subTest(case=case):
                artifact = generator.build_structural_evidence_artifact(case)
                verifier = artifact["verifier"]
                rendered = "\n\n".join(artifact["messages"])

                self.assertFalse(artifact["schema_change"])
                self.assertFalse(artifact["data_write"])
                self.assertFalse(artifact["live_telegram"])
                self.assertFalse(artifact["credential_values_included"])
                self.assertEqual(len(artifact["messages"]), 3)
                self.assertEqual(verifier["coverage_pct"], 100.0)
                self.assertEqual(verifier["coverage_percent"], 100.0)
                self.assertTrue(verifier["pass"])
                self.assertEqual(verifier["missing_slots"], [])
                self.assertEqual(
                    verifier["total_visible_decision_data_layers"],
                    len(generator.STRUCTURAL_EVIDENCE_LAYERS),
                )
                for slot in artifact["evidence_manifest"]:
                    for key in generator.STRUCTURAL_EVIDENCE_REQUIRED_KEYS:
                        self.assertIn(key, slot)
                        self.assertNotIn(slot[key], ["", [], None])

                if case == "missing_strategy_sample_source":
                    fields = {slot["field_name"]: slot for slot in artifact["evidence_manifest"]}
                    self.assertEqual(fields["evidence.strategy_sample"]["source_status"], "missing-source")
                    self.assertFalse(fields["evidence.strategy_sample"]["decision_eligible"])
                    self.assertIn("新倉：無有效進場", rendered)
                    self.assertNotIn("建準｜可買", rendered)
                    self.assertNotIn("買點：可買", rendered)
                if case == "ledger_position_conflict":
                    fields = {slot["field_name"]: slot for slot in artifact["evidence_manifest"]}
                    self.assertEqual(fields["stock.智原.execution_memory"]["source_status"], "unresolved-conflict")
                    self.assertEqual(fields["stock.智原.execution_memory"]["conflict"], "position-vs-event")
                    self.assertEqual(fields["source.conflict"]["source_status"], "unresolved-conflict")
                    self.assertNotIn("已確認停利", rendered)

    def test_v20_4_18_verifier_blocks_pass_and_actionable_entry_wording(self):
        artifact = generator.build_structural_evidence_artifact("missing_strategy_sample_source")
        messages = list(artifact["messages"])
        for injected in ["建準｜通過｜來源不足仍升格", "建準｜有效進場｜來源不足仍升格"]:
            with self.subTest(injected=injected):
                tampered = list(messages)
                tampered[1] = f"{tampered[1]}\n{injected}"
                verifier = generator.verify_structural_evidence_coverage(
                    tampered,
                    artifact["evidence_manifest"],
                )

                self.assertEqual(verifier["coverage_pct"], 100.0)
                self.assertEqual(verifier["coverage_percent"], 100.0)
                self.assertFalse(verifier["pass"])
                self.assertEqual(verifier["missing_slots"], [])
                self.assertTrue(verifier["fail_closed_violations"])

    def test_v20_4_20_maturity_report_scores_100_for_readonly_fail_closed_cases(self):
        for case in [
            "production_all_sources_available",
            "strategy_sample_missing_source",
            "ledger_position_conflict",
        ]:
            with self.subTest(case=case):
                report = generator.build_evidence_maturity_report(case)
                rendered = "\n\n".join(report["telegram_messages"])

                self.assertEqual(report["artifact_type"], "evidence_chain_maturity_report")
                self.assertEqual(report["generator_version"], generator.VERSION)
                self.assertFalse(report["schema_change"])
                self.assertFalse(report["data_write"])
                self.assertFalse(report["live_telegram"])
                self.assertFalse(report["credential_values_included"])
                self.assertEqual(report["maturity_score"], 100)
                self.assertEqual(report["blocking_findings"], [])
                self.assertEqual(
                    sorted(report["dimensions"]),
                    sorted(generator.EVIDENCE_MATURITY_DIMENSIONS),
                )
                for dimension in report["dimensions"].values():
                    self.assertEqual(dimension, {"score": 100, "status": "pass"})
                self.assertEqual(len(report["telegram_messages"]), 3)
                self.assertIn("【持倉標的】", report["telegram_messages"][0])
                self.assertIn("【未持倉標的】", report["telegram_messages"][1])
                self.assertNotIn("資料依據", report["telegram_messages"][2])
                fields = {
                    slot["field_name"]: slot
                    for slot in report["structural_artifact"]["evidence_manifest"]
                }
                self.assertIn("evidence.strategy_sample", fields)
                self.assertIn("stock.智原.risk", fields)
                for term in FORBIDDEN_SHORT_EVIDENCE_TERMS:
                    self.assertNotIn(term, report["telegram_messages"][2])
                for slot in report["structural_artifact"]["evidence_manifest"]:
                    for key in ["source", "status", "use", "limit", "conflict"]:
                        self.assertIn(key, slot)
                for artifact in report["artifacts"]:
                    self.assertFalse(artifact["schema_change"])
                    self.assertFalse(artifact["data_write"])
                    self.assertFalse(artifact["live_telegram"])
                    self.assertFalse(artifact["credential_values_included"])
                    self.assertTrue(artifact["verifier_result"]["pass"])

                if case == "strategy_sample_missing_source":
                    strategy_artifact = report["artifacts"][0]
                    self.assertEqual(strategy_artifact["status"], "missing-source")
                    self.assertEqual(strategy_artifact["use"], "不納入買賣判斷")
                    self.assertNotIn("建準｜可買", rendered)
                    self.assertNotIn("買點：可買", rendered)
                if case == "ledger_position_conflict":
                    ledger_artifact = report["artifacts"][1]
                    self.assertEqual(ledger_artifact["status"], "unresolved-conflict")
                    self.assertEqual(ledger_artifact["conflict"], "position-vs-events")
                    self.assertNotIn("已確認停利", rendered)
                    self.assertNotIn("可賣股數", rendered)

    def test_v20_4_20_maturity_report_blocks_synthetic_strategy_and_stale_runner(self):
        synthetic_report = generator.build_evidence_maturity_report("strategy_sample_synthetic_only")
        stale_report = generator.build_evidence_maturity_report("runner_stale_artifact_blocked")

        self.assertEqual(synthetic_report["maturity_score"], 0)
        self.assertEqual(
            synthetic_report["dimensions"]["strategy_sample_evidence"],
            {"score": 0, "status": "blocked"},
        )
        self.assertIn(
            "strategy sample is synthetic-only and cannot pass production maturity",
            synthetic_report["blocking_findings"],
        )
        self.assertEqual(synthetic_report["artifacts"][0]["source_type"], "synthetic")
        self.assertFalse(synthetic_report["artifacts"][0]["verifier_result"]["pass"])

        self.assertEqual(stale_report["maturity_score"], 0)
        self.assertEqual(
            stale_report["dimensions"]["repeatable_runner_process"],
            {"score": 0, "status": "blocked"},
        )
        self.assertEqual(stale_report["artifacts"][2]["status"], "unresolved-conflict")
        self.assertEqual(stale_report["artifacts"][2]["conflict"], "stale-handoff-artifact")
        self.assertIn("stale handoff/artifact must block maturity completion", stale_report["blocking_findings"])

    def test_v20_4_10_manifest_fails_closed_for_missing_candidate_sources(self):
        payload = {
            "stock_code": "2421",
            "price": None,
            "change": None,
            "price_source": None,
            "daily_source": None,
            "result": {
                "decision": "BUY",
                "action": 0.1,
                "rr": 1.8,
                "heat_state": "NORMAL",
                "trade_state": "READY",
                "structure_phase": "BREAKOUT_CONFIRM",
                "price_behavior": "NORMAL",
                "market_grade": "A",
                "volume_state": "STRONG",
                "volume_price_state": "EXPANSION",
                "structure_state": "STRONG",
                "entry_quality": "A",
                "confidence_score": 86,
            },
            "holding": None,
            "structure_score": 5,
            "volume_ratio": 1.4,
            "closes": [],
            "volumes": [],
        }

        context = generator.build_report_context(
            {"建準": payload},
            {
                "market_theme_evidence": {
                    "status": "confirmed",
                    "theme_status": "confirmed",
                    "source_of_truth": "production_db",
                },
            },
            datetime(2026, 5, 31),
            strategy_evidence_summary=AVAILABLE_STRATEGY_EVIDENCE,
            report_phase="盤中",
        )
        fields = {item["field_name"]: item for item in context["evidence_manifest"]}

        self.assertEqual(fields["stock.建準.price"]["source_status"], "insufficient-data")
        self.assertFalse(fields["stock.建準.price"]["decision_eligible"])
        self.assertEqual(fields["stock.建準.rr"]["source_status"], "insufficient-data")
        self.assertFalse(fields["stock.建準.rr"]["decision_eligible"])
        self.assertEqual(fields["funnel.unheld_counts"]["source_status"], "insufficient-data")
        self.assertEqual(fields["evidence.strategy_sample"]["source_status"], "available")
        self.assertFalse(fields["tomorrow.plan"]["decision_eligible"])

        messages = generator.formatTelegramMessages(
            {"建準": payload},
            "FULL DETAIL",
            "建準",
            88,
            {
                "market_theme_evidence": {
                    "status": "confirmed",
                    "theme_status": "confirmed",
                    "source_of_truth": "production_db",
                },
            },
            datetime(2026, 5, 31),
            strategy_evidence_summary=AVAILABLE_STRATEGY_EVIDENCE,
            report_phase="盤中",
        )
        joined = "\n\n".join(messages)
        summary = summary_message(messages)
        unheld = unheld_message(messages)

        self.assertIs(messages[2], summary)
        self.assertIn("【05/31 盤中｜v20.4.47】", summary)
        self.assertNotIn("Source：核心價格 insufficient-data", summary)
        self.assertIn("新倉：無有效進場", summary)
        self.assertNotIn("🔥 最強", summary)
        self.assertNotIn("排序★", summary)
        self.assertNotIn("評級★", summary)
        self.assertNotIn("交易執行 1", summary)
        self.assertNotIn("建準｜可買", summary)
        self.assertNotIn("Source：漏斗 count", summary)
        self.assertIn("【建準 2421】⛔ 不可行動｜資料來源缺失", unheld)
        self.assertIn("買點：不可買，資料來源缺失", unheld)
        self.assertIn("資料：缺現價/OHLCV，停止新倉判斷", unheld)
        self.assertNotIn("Source：price insufficient-data｜OHLCV insufficient-data｜RR insufficient-data", unheld)
        self.assertNotIn("建準｜可買", joined)
        self.assertNotIn("買點：可買", joined)
        self.assertNotIn("建議 10%倉", joined)
        self.assertNotIn("現在可分批", joined)

    def test_v20_4_10_summary_hides_strongest_when_candidate_source_missing(self):
        payload = {
            "stock_code": "2421",
            "price": 100,
            "change": 0,
            "price_source": "runtime-cache",
            "daily_source": "runtime-cache",
            "result": {
                "decision": "BUY",
                "action": 0.1,
                "rr": 1.8,
                "heat_state": "NORMAL",
                "trade_state": "READY",
                "structure_phase": "BREAKOUT_CONFIRM",
                "price_behavior": "NORMAL",
                "market_grade": "A",
                "volume_state": "STRONG",
                "volume_price_state": "EXPANSION",
                "structure_state": "STRONG",
                "entry_quality": "A",
                "confidence_score": 86,
                "strength": 92,
            },
            "holding": None,
            "structure_score": 5,
            "volume_ratio": 1.4,
            "closes": [90, 91, 92, 93, 94],
            "volumes": [1000, 1100, 1200, 1300, 1400],
        }

        messages = generator.formatTelegramMessages(
            {"建準": payload},
            "FULL DETAIL",
            "建準",
            88,
            {
                "market_theme_evidence": {
                    "status": "confirmed",
                    "theme_status": "confirmed",
                    "source_of_truth": "production_db",
                },
            },
            datetime(2026, 5, 31),
            strategy_evidence_summary=None,
            report_phase="盤中",
        )
        summary = summary_message(messages)
        unheld = unheld_message(messages)

        self.assertIs(messages[2], summary)
        self.assertNotIn("Source：核心價格 insufficient-data", summary)
        self.assertIn("新倉：無有效進場", summary)
        self.assertNotIn("🔥 最強", summary)
        self.assertNotIn("排序★", summary)
        self.assertNotIn("評級★", summary)
        self.assertIn("買點：不可買，資料來源缺失", unheld)
        self.assertIn("資料：缺現價/OHLCV，停止新倉判斷", unheld)
        self.assertNotIn("Source：price missing-source｜OHLCV missing-source｜RR missing-source", unheld)

    def test_v20_4_20_summary_hides_strongest_when_candidate_not_valid_entry(self):
        payload = {
            "stock_code": "2421",
            "price": 100,
            "change": 0,
            "price_source": "realtime",
            "daily_source": "yahoo",
            "result": {
                "decision": "WAIT",
                "action": 0,
                "rr": 2.4,
                "heat_state": "NORMAL",
                "trade_state": "WATCH",
                "structure_phase": "BREAKOUT_WATCH",
                "price_behavior": "NORMAL",
                "market_grade": "A",
                "volume_state": "NORMAL",
                "volume_price_state": "NORMAL",
                "structure_state": "STRONG",
                "entry_quality": "B",
                "confidence_score": 80,
                "strength": 88,
            },
            "holding": None,
            "structure_score": 5,
            "volume_ratio": 1.2,
            "closes": [90, 91, 92, 93, 94, 95, 96, 97, 98, 100],
            "volumes": [1000, 1020, 1040, 1060, 1080, 1100, 1120, 1140, 1160, 1180],
        }

        messages = generator.formatTelegramMessages(
            {"建準": payload},
            "FULL DETAIL",
            "建準",
            88,
            {
                "market_theme_evidence": {
                    "status": "confirmed",
                    "theme_status": "confirmed",
                    "source_of_truth": "production_db",
                },
            },
            datetime(2026, 5, 31),
            strategy_evidence_summary=None,
            report_phase="盤中",
        )
        summary = summary_message(messages)

        self.assertIn("新倉：無有效進場", summary)
        self.assertNotIn("🔥 最強", summary)
        self.assertNotIn("排序★", summary)
        self.assertNotIn("評級★", summary)

    def test_v20_4_16_unheld_card_fails_closed_when_ohlcv_missing(self):
        payload = {
            "stock_code": "2421",
            "price": 100,
            "change": 0,
            "price_source": "realtime",
            "daily_source": "yahoo",
            "result": {
                "decision": "BUY",
                "action": 0.1,
                "rr": 1.8,
                "heat_state": "NORMAL",
                "trade_state": "READY",
                "structure_phase": "BREAKOUT_CONFIRM",
                "price_behavior": "NORMAL",
                "market_grade": "A",
                "volume_state": "STRONG",
                "volume_price_state": "EXPANSION",
                "structure_state": "STRONG",
                "entry_quality": "A",
                "confidence_score": 86,
                "strength": 92,
            },
            "holding": None,
            "structure_score": 5,
            "volume_ratio": 1.4,
            "closes": [],
            "volumes": [],
        }

        messages = generator.formatTelegramMessages(
            {"建準": payload},
            "FULL DETAIL",
            "建準",
            88,
            {
                "market_theme_evidence": {
                    "status": "confirmed",
                    "theme_status": "confirmed",
                    "source_of_truth": "production_db",
                },
            },
            datetime(2026, 5, 31),
            strategy_evidence_summary=None,
            report_phase="盤中",
        )
        joined = "\n\n".join(messages)
        unheld = unheld_message(messages)

        self.assertIn("【建準 2421】⛔ 不可行動｜資料來源缺失", unheld)
        self.assertIn("買點：不可買", unheld)
        self.assertIn("資料：缺OHLCV，停止新倉判斷", unheld)
        self.assertNotIn("Source：", unheld)
        self.assertNotIn("買點：可買", joined)
        self.assertNotIn("建議 10%倉", joined)

    def test_v20_4_10_mixed_valid_and_source_ineligible_buy_like_stays_consistent(self):
        valid_payload = {
            "stock_code": "2301",
            "price": 70,
            "change": 2.0,
            "price_source": "realtime",
            "daily_source": "yahoo",
            "result": {
                "decision": "BUY",
                "action": 0.1,
                "rr": 2.4,
                "heat_state": "NORMAL",
                "trade_state": "READY",
                "structure_phase": "BREAKOUT_CONFIRM",
                "price_behavior": "NORMAL",
                "market_grade": "A",
                "volume_state": "STRONG",
                "volume_price_state": "EXPANSION",
                "structure_state": "STRONG",
                "entry_quality": "A",
                "confidence_score": 86,
                "strength": 91,
            },
            "holding": None,
            "structure_score": 5,
            "volume_ratio": 1.6,
            "closes": [50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 70],
            "volumes": VOL_ATTACK,
        }
        invalid_payload = {
            "stock_code": "2421",
            "price": 100.0,
            "change": 1.2,
            "price_source": "runtime-cache",
            "daily_source": "runtime-cache",
            "result": {
                "decision": "BUY",
                "action": 0.1,
                "rr": 2.1,
                "heat_state": "NORMAL",
                "trade_state": "READY",
                "structure_phase": "BREAKOUT_CONFIRM",
                "price_behavior": "NORMAL",
                "market_grade": "A",
                "volume_state": "STRONG",
                "volume_price_state": "EXPANSION",
                "structure_state": "STRONG",
                "entry_quality": "A",
                "confidence_score": 88,
                "strength": 95,
            },
            "holding": None,
            "structure_score": 5,
            "volume_ratio": 1.5,
            "closes": [90, 91, 92, 93, 94],
            "volumes": [1000, 1100, 1200, 1300, 1400],
        }

        messages = generator.formatTelegramMessages(
            {"光寶科": valid_payload, "建準": invalid_payload},
            "FULL DETAIL",
            "建準",
            95,
            {
                "market_theme_evidence": {
                    "status": "confirmed",
                    "theme_status": "confirmed",
                    "source_of_truth": "production_db",
                },
            },
            datetime(2026, 5, 31),
            strategy_evidence_summary=AVAILABLE_STRATEGY_EVIDENCE,
            report_phase="盤中",
        )
        summary = summary_message(messages)
        unheld = unheld_message(messages)
        invalid_card = unheld[unheld.index("【建準 2421】"):]
        invalid_card = invalid_card.split("\n\n【", 1)[0]

        self.assertIn("新倉建議 1", summary)
        self.assertNotIn("✅ 今日盤中交易執行\n光寶科", summary)
        self.assertIn("光寶科 可買（分批，不追價）", summary)
        self.assertNotIn("新倉：無有效進場", summary)
        self.assertNotIn("🔥 最強", summary)
        self.assertIn("未持倉 2｜可買 1｜淘汰 1", summary)
        self.assertNotIn("Source：漏斗 count", summary)
        self.assertIn("【建準 2421】⛔ 不可行動｜資料來源缺失", invalid_card)
        self.assertIn("買點：不可買，資料來源缺失", invalid_card)
        self.assertIn("卡關主因：資料來源缺失", invalid_card)
        self.assertIn("量化差距：需補齊有效行情 / 策略來源", invalid_card)
        self.assertIn("價格：不可用（資料來源缺失）", invalid_card)
        self.assertNotIn("missing-source", invalid_card)
        self.assertIn("數據：RR 不可用｜S 不可用｜V 不可用", invalid_card)
        self.assertNotIn("RR 2.1", invalid_card)
        self.assertNotIn("S 5/5", invalid_card)
        self.assertNotIn("V 1.5x", invalid_card)
        self.assertNotIn("價格：100", invalid_card)

    def test_v20_4_25_strategy_sample_source_error_blocks_action_without_hiding_available_price(self):
        payload = {
            "stock_code": "2421",
            "price": 100.0,
            "change": 1.2,
            "price_source": "realtime",
            "daily_source": "yahoo",
            "result": {
                "decision": "BUY",
                "action": 0.1,
                "rr": 2.1,
                "heat_state": "NORMAL",
                "trade_state": "READY",
                "structure_phase": "BREAKOUT_CONFIRM",
                "price_behavior": "NORMAL",
                "market_grade": "A",
                "volume_state": "STRONG",
                "volume_price_state": "EXPANSION",
                "structure_state": "STRONG",
                "entry_quality": "A",
                "confidence_score": 88,
                "strength": 95,
            },
            "holding": None,
            "structure_score": 5,
            "volume_ratio": 1.5,
            "closes": [90, 91, 92, 93, 94, 95, 96, 97, 98, 100],
            "volumes": [1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900],
        }

        messages = generator.formatTelegramMessages(
            {"建準": payload},
            "FULL DETAIL",
            "建準",
            95,
            {
                "market_theme_evidence": {
                    "status": "confirmed",
                    "theme_status": "confirmed",
                    "source_of_truth": "production_db",
                },
            },
            datetime(2026, 5, 31),
            strategy_evidence_summary=structured_strategy_evidence(
                "source-error",
                row_count=0,
                rendered_text="策略樣本讀取失敗｜source-error",
            ),
            report_phase="盤中",
        )
        rendered = "\n\n".join(messages)
        summary = summary_message(messages)
        card = card_block(unheld_message(messages), "【建準 2421】")

        self.assertIn("新倉：無有效進場", summary)
        self.assertNotIn("建準｜可買", summary)
        self.assertNotIn("建準｜可買", rendered)
        self.assertIn("【建準 2421】⛔ 不可行動｜策略樣本來源異常", card)
        self.assertIn("盤面：證據不足｜待確認", card)
        self.assertIn("買點：不可買，策略樣本來源讀取異常", card)
        self.assertIn("卡關主因：樣本不足", card)
        self.assertIn("量化差距：需更多有效策略樣本確認", card)
        self.assertIn("原因：策略樣本不可用，高置信 S 分數 / 強弱分類暫不採用", card)
        self.assertIn("盤中觸發：無有效進場，先補策略樣本證據", card)
        self.assertIn("數據：RR：-（不可行動）｜S 證據不足｜V 1.5x", card)
        self.assertIn("價格：100.0（+1.20%）", card)
        self.assertNotIn("價格：不可用（資料來源缺失）", card)
        self.assertNotIn("source missing", card)
        self.assertNotIn("S 5/5", card)
        self.assertNotIn("突破確認", card)

    def test_v20_4_27_strategy_sample_status_uses_structured_status_not_rendered_text(self):
        structured = {
            "rendered_text": "策略樣本：來源可驗證｜但文字不應被解析",
            "structured_status": {
                "status": "source-error",
                "source": "daily_signal_snapshot",
                "row_count": 30,
                "as_of": "2026-06-02",
                "missing_fields": [],
            },
        }

        status, reason = generator._strategy_sample_status(structured)
        legacy_status, legacy_reason = generator._strategy_sample_status("策略樣本：來源可驗證｜樣本 30")

        self.assertEqual(status, "source-error")
        self.assertIn("daily_signal_snapshot", reason)
        self.assertEqual(legacy_status, "missing-source")
        self.assertIn("未用文字摘要反推", legacy_reason)

    def test_v20_4_27_last_ohlcv_fallback_is_stale_and_not_actionable(self):
        cached = {
            "stock_id": "2421",
            "trade_date": datetime(2026, 5, 29).date(),
            "open": 99.0,
            "high": 101.0,
            "low": 98.0,
            "close": 100.0,
            "volume": 1000,
            "source": "yahoo",
        }

        with patch.object(generator, "get_yahoo_history", return_value=None), \
             patch.object(generator, "get_twse", return_value=None), \
             patch.object(generator, "get_last_error", return_value="daily: source-error"), \
             patch.object(generator, "last_ohlcv_fallback_payload", return_value={**cached, "stale": True, "data_date": "2026-05-29", "fallback_source": "LAST_OHLCV"}), \
             patch.object(generator, "get_realtime_price", return_value=None), \
             patch.object(generator, "get_yahoo", return_value=None):
            name, data, _decision, error = generator.load_stock_signal("建準", "2421")

        self.assertEqual(name, "建準")
        self.assertIsNone(error)
        self.assertEqual(data["daily_source"], "LAST_OHLCV")
        self.assertEqual(data["price_source"], "LAST_OHLCV")
        self.assertTrue(data["ohlcv"]["stale"])
        self.assertEqual(data["ohlcv"]["data_date"], "2026-05-29")

        messages = generator.formatTelegramMessages(
            {"建準": data},
            "FULL DETAIL",
            "建準",
            95,
            {"trade_date": "2026-06-02"},
            datetime(2026, 6, 2),
            strategy_evidence_summary=AVAILABLE_STRATEGY_EVIDENCE,
            report_phase="盤中",
        )
        rendered = "\n\n".join(messages)
        self.assertIn("建準 使用 LAST_OHLCV 2026-05-29，非當日資料", summary_message(messages))
        self.assertNotIn("建準｜可買", rendered)
        self.assertNotIn("買點：可買", rendered)

    def test_v20_4_27_phone_reading_noise_and_zero_placeholders_are_compressed(self):
        payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119],
            None,
            price=119,
            change=1.4,
        )
        payload["stock_code"] = "2421"
        payload["result"].update({
            "decision": "WAIT",
            "action": 0,
            "rr": 0.4,
            "trade_state": "LATE_ENTRY",
            "heat_state": "HOT",
        })

        messages = generator.formatTelegramMessages(
            {"建準": payload},
            "FULL DETAIL",
            None,
            None,
            {"trade_date": "2026-06-02", "market_theme_evidence": {"status": "insufficient-data", "source_status": "insufficient-data"}},
            datetime(2026, 6, 2),
            strategy_evidence_summary=structured_strategy_evidence("source-error", row_count=0),
            report_phase="盤中",
        )
        summary = summary_message(messages)
        evidence = evidence_message(messages)
        rendered = "\n\n".join(messages)

        self.assertLessEqual(sum(1 for line in summary.splitlines() if line.startswith("🧭 新倉")), 1)
        self.assertLessEqual(rendered.count("新倉：無有效進場"), 2)
        self.assertNotIn("無新增下單", rendered)
        self.assertIn("執行動作 0｜今日新建倉 0", rendered)
        self.assertNotIn("僅追蹤 0", rendered)
        self.assertEqual(evidence.count("策略樣本："), 0)
        self.assertNotIn("可靠度中等", evidence)
        self.assertNotIn("已突破（-", rendered)

    def test_source_missing_no_empty_execution_placeholder_and_hides_all_zero_unheld_funnel(self):
        messages = generator._source_missing_report_messages(
            datetime(2026, 6, 2),
            "盤中",
            "missing positions source",
        )
        brief = messages[2]
        rendered = "\n\n".join(messages)

        self.assertEqual(generator.format_unheld_funnel([]), "")
        self.assertNotIn("✅ 今日盤中交易執行", brief)
        self.assertNotIn("✅ 今日盤中交易執行", rendered)
        self.assertNotIn("無新增下單", brief)
        self.assertNotIn("無新增下單", rendered)
        self.assertNotIn("交易執行：無新增下單", rendered)
        self.assertNotIn("未持倉漏斗（非執行）", brief)
        self.assertNotIn("未持倉總數 0 檔", rendered)
        self.assertNotIn("可買 0｜不可追高觀察 0（不可買）｜僅追蹤 0｜淘汰 0", rendered)
        self.assertNotIn("僅追蹤 0", rendered)

    def test_presentation_noise_intraday_no_valid_entry_uses_track_only_without_data_basis(self):
        payload = self.evidence_payload(confidence=64, decision="WAIT", action=0, rr=1.2, distance=3)
        payload["cross_day_context"] = {
            "source_status": "ready",
            "source_of_truth": ["daily_signal_snapshot"],
            "previous_action": "observe",
            "consecutive_observe_days": 2,
            "repair_status": "improving",
        }

        with patch.object(generator, "market_theme_summary_evidence", return_value=self.confirmed_market_evidence()):
            messages = generator.formatTelegramMessages(
                {"追蹤股": payload},
                "FULL DETAIL",
                None,
                None,
                {"trade_date": "2026-06-02"},
                datetime(2026, 6, 2),
                strategy_evidence_summary=structured_strategy_evidence("available", row_count=30),
                report_phase="盤中",
            )

        summary = summary_message(messages)
        unheld = unheld_message(messages)
        rendered = "\n\n".join(messages)
        self.assertIn(f"🧾 {generator.VERSION} 簡報", summary)
        self.assertNotIn("資料依據", summary)
        self.assertNotIn("追蹤最強", rendered)
        self.assertIn("市場：中性觀察 R2｜執行動作 0｜今日新建倉 0｜持倉風控 0｜未持倉 1", summary)
        self.assertNotIn("新倉：目前沒有可行動候選", summary)
        self.assertNotIn("僅追蹤：\n- 追蹤股（修復中｜連續觀察 2 天，未達進場條件）", summary)
        self.assertIn("【追蹤股 9999】", unheld)
        self.assertNotIn("回測：-", unheld)
        self.assertNotIn("策略樣本：不可用，本次不納入判斷", unheld)

    def test_presentation_noise_afterhours_normal_sources_hide_data_basis(self):
        payload = self.evidence_payload(confidence=64, decision="WAIT", action=0, rr=1.2, distance=4)

        with patch.object(generator, "market_theme_summary_evidence", return_value=self.confirmed_market_evidence()):
            messages = generator.formatTelegramMessages(
                {"觀察股": payload},
                "FULL DETAIL",
                None,
                None,
                {"trade_date": "2026-06-02"},
                datetime(2026, 6, 2),
                strategy_evidence_summary=structured_strategy_evidence("available", row_count=30),
                report_phase="盤後",
            )

        brief = summary_message(messages)
        self.assertIn(f"🧾 {generator.VERSION} 簡報", brief)
        self.assertNotIn("資料依據", brief)
        self.assertIn("📌 盤後簡報", brief)
        self.assertIn("新增有效進場：無", brief)
        self.assertNotIn("市場 / 題材背景：", brief)
        self.assertNotIn("策略樣本：", brief)

    def test_presentation_noise_afterhours_source_error_keeps_manifest_and_hides_data_basis(self):
        payload = self.evidence_payload(confidence=64, decision="WAIT", action=0, rr=1.2, distance=4)

        with patch.object(generator, "market_theme_summary_evidence", return_value=self.confirmed_market_evidence()):
            messages = generator.formatTelegramMessages(
                {"來源異常": payload},
                "FULL DETAIL",
                None,
                None,
                {"trade_date": "2026-06-02"},
                datetime(2026, 6, 2),
                strategy_evidence_summary=structured_strategy_evidence("source-error", row_count=0),
                report_phase="盤後",
            )
            context = generator.build_report_context(
                {"來源異常": payload},
                {"trade_date": "2026-06-02"},
                datetime(2026, 6, 2),
                strategy_evidence_summary=structured_strategy_evidence("source-error", row_count=0),
                report_phase="盤後",
            )

        brief = summary_message(messages)
        unheld = unheld_message(messages)
        fields = {slot["field_name"]: slot for slot in context["evidence_manifest"]}
        self.assertIn(f"🧾 {generator.VERSION} 簡報", brief)
        self.assertNotIn("資料依據", brief)
        self.assertEqual(fields["evidence.strategy_sample"]["source_status"], "source-error")
        self.assertFalse(fields["evidence.strategy_sample"]["decision_eligible"])
        self.assertNotIn("策略樣本：不可用，本次不納入判斷", unheld)

    def test_presentation_noise_card_history_unavailable_hidden_across_cards(self):
        sample_a = self.evidence_payload(confidence=61, decision="WAIT", action=0, rr=1.0, distance=8)
        sample_b = self.evidence_payload(confidence=62, decision="WAIT", action=0, rr=1.1, distance=9)
        sample_a["backtest_context"] = {"sample": 3, "win_rate": 50, "avg_return": 0.1}
        sample_b["backtest_context"] = None

        with patch.object(generator, "market_theme_summary_evidence", return_value=self.confirmed_market_evidence()):
            messages = generator.formatTelegramMessages(
                {"樣本不足": sample_a, "無歷史": sample_b},
                "FULL DETAIL",
                None,
                None,
                {"trade_date": "2026-06-02"},
                datetime(2026, 6, 2),
                strategy_evidence_summary=structured_strategy_evidence("available", row_count=30),
                report_phase="盤中",
            )

        unheld = unheld_message(messages)
        self.assertNotIn("回測：不可用", unheld)
        self.assertNotIn("回測：-", unheld)
        self.assertNotIn("樣本不足（有效樣本3）", unheld)

    def test_telegram_message_noise_consistency_intraday_owner_nine_points(self):
        holding = render_payload(
            [40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 65],
            {"shares": 550, "avg_price": 52.15},
            price=65.4,
            change=9.9,
        )
        holding["stock_code"] = "2337"
        holding["holding_decision"] = {
            "action": "減碼",
            "level": "REDUCE_25",
            "note": "續降優先級",
            "warning_price": 62.13,
            "hard_stop_price": 58.86,
        }
        tracking = self.evidence_payload(confidence=64, decision="WAIT", action=0, rr=1.2, distance=2, heat="HOT")
        tracking["stock_code"] = "0001"
        tracking["cross_day_context"] = {
            "source_status": "ready",
            "source_of_truth": ["daily_signal_snapshot"],
            "previous_state": "eliminated",
            "repair_status": "improving",
            "consecutive_observe_days": 1,
            "weight_reason": ["修復中", "連續觀察 1 天"],
        }
        tracking["backtest_context"] = {
            "version": "v19.1",
            "scope": "同型",
            "setup": "突破確認/放量/已突破",
            "sample": 15,
            "win_rate": 55,
            "avg_return": 0.8,
            "metric": "3日相對股票池",
            "verdict": "偏強",
            "action": "只作參考",
        }
        rejected = self.evidence_payload(confidence=45, decision="FAIL", action=0, rr=3.06, distance=9)
        rejected["stock_code"] = "2301"
        rejected["result"].update({
            "structure_phase": "FAILED_BREAKOUT",
            "price_behavior": "WEAK_REBOUND",
            "market_grade": "D",
            "reject_family": "突破失敗",
        })
        partial = self.evidence_payload(confidence=68, decision="WAIT", action=0, rr=1.1, distance=2, heat="HOT")
        partial["stock_code"] = "0002"
        partial["market_theme_evidence"] = self.confirmed_market_evidence("single_day")
        partial["strategy_sample_evidence"] = {
            "source_status": "available",
            "sample": 9,
            "win_rate": 45,
            "avg_return": 0,
            "label": "partial",
        }
        sample_missing = self.evidence_payload(confidence=62, decision="WAIT", action=0, rr=1.0, distance=2, heat="HOT")
        sample_missing["stock_code"] = "0003"
        sample_missing["backtest_context"] = {"sample": 3, "win_rate": 50, "avg_return": 0.1}
        payloads = {
            "旺宏": holding,
            "修復股": tracking,
            "光寶科": rejected,
            "輔助股": partial,
            "樣本不足": sample_missing,
        }

        with patch.object(generator, "market_theme_summary_evidence", return_value=self.confirmed_market_evidence()):
            messages = generator.formatTelegramMessages(
                payloads,
                "FULL DETAIL",
                None,
                None,
                {"trade_date": "2026-06-03"},
                datetime(2026, 6, 3),
                strategy_evidence_summary=structured_strategy_evidence("available", row_count=30),
                report_phase="盤中",
            )

        brief = summary_message(messages)
        rendered = "\n\n".join(messages)
        unheld = unheld_message(messages)
        holding_card = position_message(messages)
        first_market_line = first_line_for_prefix(brief, "市場：")
        tracking_card = card_block(unheld, "【修復股")
        rejected_card = card_block(unheld, "【光寶科")
        partial_card = card_block(unheld, "【輔助股")

        self.assertEqual(brief.count("市場："), 1)
        self.assertIn("市場：進攻偏熱 R3｜執行動作 1（減碼）｜今日新建倉 0｜持倉風控 1｜未持倉 4（僅追蹤3/淘汰1）", first_market_line)
        self.assertNotIn("進攻偏熱｜R3", first_market_line)
        self.assertNotIn("R3 進攻偏熱", first_market_line)
        for redundant in ["新倉：目前沒有可行動候選", "背景：", "📌 持倉：", "未持倉 3 檔只等觸發"]:
            self.assertNotIn(redundant, brief)
        self.assertIn("交易執行\n旺宏 減碼（續降優先級）", brief)
        self.assertNotIn("旺宏｜+9.24%｜減碼｜續降優先級", brief)
        self.assertNotIn("僅追蹤：\n- 修復股（修復中｜連續觀察 1 天，未達進場條件）", brief)
        self.assertIn("未持倉 4｜", brief)
        self.assertIn("未持倉 4｜僅追蹤 3（等冷卻）｜淘汰 1", brief)
        self.assertIn("未持倉 4（僅追蹤3/淘汰1）", brief)
        self.assertIn("RR：-（不可行動）", rejected_card)
        self.assertNotIn("RR 3.06", rejected_card)
        self.assertNotIn("回測：", tracking_card)
        self.assertIn("回測（修復股）：樣本15｜參考度中｜3日勝率55%｜相對+0.8%｜無明顯優勢", brief)
        self.assertNotIn("回測：不可用", unheld)
        self.assertNotIn("樣本不足（有效樣本3）", unheld)
        self.assertIn("證據：過熱不適用", partial_card)
        self.assertNotIn("證據 +0%", partial_card)
        self.assertEqual(tracking_card.count("修復中"), 1)
        self.assertEqual(tracking_card.count("連續觀察 1 天"), 1)
        self.assertIn("【旺宏 2337】📌 減碼", holding_card)
        self.assertNotIn("📊 策略證據 v20.0", rendered)

    def test_telegram_message_noise_consistency_afterhours_reuses_compact_brief(self):
        tracking = self.evidence_payload(confidence=64, decision="WAIT", action=0, rr=1.2, distance=2, heat="HOT")
        rejected = self.evidence_payload(confidence=45, decision="FAIL", action=0, rr=3.06, distance=9)
        rejected["stock_code"] = "2301"
        rejected["result"].update({
            "structure_phase": "FAILED_BREAKOUT",
            "price_behavior": "WEAK_REBOUND",
            "market_grade": "D",
            "reject_family": "突破失敗",
        })

        with patch.object(generator, "market_theme_summary_evidence", return_value=self.confirmed_market_evidence()):
            messages = generator.formatTelegramMessages(
                {"追蹤股": tracking, "光寶科": rejected},
                "FULL DETAIL",
                None,
                None,
                {"trade_date": "2026-06-03"},
                datetime(2026, 6, 3),
                strategy_evidence_summary=structured_strategy_evidence("available", row_count=30),
                report_phase="盤後",
            )

        brief = summary_message(messages)
        rejected_card = card_block(unheld_message(messages), "【光寶科")
        self.assertIn("市場：進攻偏熱 R3", brief)
        self.assertIn("未持倉 2（僅追蹤1/淘汰1）", brief)
        self.assertNotIn("背景：", brief)
        self.assertNotIn("新倉：目前沒有可行動候選", brief)
        self.assertIn("RR：-（不可行動）", rejected_card)
        self.assertNotIn("RR 3.06", rejected_card)

    def test_0603_v20_4_32_failure_specimen_message_list_replay(self):
        umc = render_payload(
            [150, 149, 148, 147, 146, 145, 144, 143, 142, 141, 140, 139, 138, 137, 136, 135, 134, 133.5, 133, 132.75],
            {"shares": 50, "avg_price": 138.08},
            price=132.75,
            change=-3.86,
        )
        umc["stock_code"] = "2303"
        umc["position_events"] = {"event_count": 1, "bought_shares": 50}
        umc["result"].update({
            "decision": "FAIL",
            "structure_phase": "FAILED_BREAKOUT",
            "price_behavior": "WEAK_REBOUND",
            "market_grade": "D",
            "volume_state": "WEAK",
            "volume_price_state": "DISTRIBUTION",
            "rr": 0.6,
        })

        gigabyte = self.evidence_payload(confidence=63, decision="WAIT", action=0, rr=0.21, distance=2, heat="HOT")
        gigabyte["stock_code"] = "2376"
        gigabyte["price"] = 336.25
        gigabyte["change"] = -0.07
        gigabyte["result"].update({
            "trade_state": "EXTENDED",
            "structure_phase": "BREAKOUT_CONFIRM",
            "calc_rr": 0.21,
        })

        insufficient = self.evidence_payload(confidence=62, decision="WAIT", action=0, rr=1.0, distance=3, heat="NORMAL")
        insufficient["stock_code"] = "9991"
        insufficient["backtest_context"] = {"sample": 3, "win_rate": 50, "avg_return": 0.1}
        unavailable = self.evidence_payload(confidence=61, decision="WAIT", action=0, rr=1.1, distance=4, heat="NORMAL")
        unavailable["stock_code"] = "9992"
        unavailable["backtest_context"] = None
        unstable_buy = self.evidence_payload(confidence=78, decision="BUY", action=0.1, rr=1.6, distance=0.5, heat="NORMAL")
        unstable_buy["stock_code"] = "2301"
        unstable_buy["result"].update({
            "trade_state": "READY",
            "market_grade": "A",
            "entry_quality": "A",
        })
        unstable_buy["cross_day_context"] = {
            "source_status": "ready",
            "source_of_truth": ["daily_signal_snapshot"],
            "previous_state": "eliminated",
            "consecutive_buy_signals": 1,
        }

        with patch.object(generator, "market_theme_summary_evidence", return_value=self.confirmed_market_evidence()):
            messages = generator.formatTelegramMessages(
                {
                    "聯電": umc,
                    "技嘉": gigabyte,
                    "樣本不足": insufficient,
                    "無歷史": unavailable,
                    "光寶科": unstable_buy,
                },
                "FULL DETAIL",
                None,
                None,
                {"trade_date": "2026-06-03"},
                datetime(2026, 6, 3),
                strategy_evidence_summary=structured_strategy_evidence("available", row_count=30),
                report_phase="盤中",
            )

        summary = summary_message(messages)
        position = position_message(messages)
        unheld = unheld_message(messages)
        rendered = "\n\n".join(messages)
        umc_card = card_block(position, "【聯電 2303】")
        gigabyte_card = card_block(unheld, "【技嘉 2376】")
        unstable_card = card_block(unheld, "【光寶科 2301】")
        reason_lines = [line for line in summary.splitlines() if line.startswith("原因：")]

        self.assertIn("【06/03 盤中｜v20.4.47】", summary)
        self.assertIn("【聯電 2303】📌 減碼", umc_card)
        self.assertIn("均價 138.08", umc_card)
        self.assertIn("價格：132.75（-3.86%）", umc_card)
        self.assertIn("今日 買 50股", umc_card)
        self.assertIn("條件：同日建倉後觸發快速止損 / 入場即錯", umc_card)
        self.assertIn("聯電｜-3.86%｜減碼", summary)
        self.assertNotIn("新倉風控觀察", umc_card + summary)
        self.assertIn("【技嘉 2376】⏳ 等冷卻｜過熱觀察", gigabyte_card)
        self.assertIn("數據：RR -（過熱）", gigabyte_card)
        self.assertNotIn("RR 0.21", gigabyte_card)
        self.assertIn("【光寶科 2301】⛔ 不買｜前態待確認", unstable_card)
        self.assertNotIn("不買｜進場", rendered)
        self.assertEqual(len(reason_lines), 1)
        self.assertNotIn("聯電：", reason_lines[0])
        self.assertNotIn("技嘉：", reason_lines[0])
        self.assertNotIn("；", reason_lines[0])
        self.assertNotIn("回測：不可用", unheld)
        self.assertNotIn("回測：-", unheld)
        self.assertNotIn("樣本不足（有效樣本3）", unheld)

    def evidence_payload(self, *, confidence=78, decision="WAIT", action=0, rr=1.4, distance=2, heat="NORMAL"):
        return {
            "stock_code": "9999",
            "price": 100,
            "change": 0,
            "price_source": "realtime",
            "daily_source": "yahoo",
            "result": {
                "decision": decision,
                "action": action,
                "rr": rr,
                "heat_state": heat,
                "trade_state": "READY",
                "structure_phase": "BREAKOUT_NEAR",
                "price_behavior": "NORMAL",
                "market_grade": "A",
                "volume_state": "STRONG",
                "volume_price_state": "EXPANSION",
                "structure_state": "STRONG",
                "entry_quality": "A",
                "confidence_score": confidence,
                "breakout_distance": distance,
            },
            "holding": None,
            "structure_score": 4,
            "volume_ratio": 1.4,
            "closes": [90, 91, 92],
            "volumes": [1000, 1100, 1200],
        }

    def test_v20_4_36_non_actionable_unheld_hides_score_numbers(self):
        low_volume = self.evidence_payload(confidence=93, decision="WAIT", action=0, rr=1.8, distance=1)
        low_volume["stock_code"] = "2301"
        low_volume["volume_ratio"] = 0.6
        low_volume["result"].update({
            "trade_state": "NO_VOLUME",
            "volume_state": "WEAK",
            "confidence_score": 93,
        })
        buyable = self.evidence_payload(confidence=82, decision="BUY", action=0.1, rr=1.8, distance=0.5)
        buyable["stock_code"] = "2421"
        buyable["backtest_context"] = {"sample": 38, "reference": "高", "win_rate": 58, "avg_return": 1.2}

        with patch.object(generator, "market_theme_summary_evidence", return_value=self.confirmed_market_evidence()):
            messages = generator.formatTelegramMessages(
                {"光寶科": low_volume, "建準": buyable},
                "",
                None,
                None,
                {"trade_date": "2026-06-04"},
                datetime(2026, 6, 4),
                strategy_evidence_summary=structured_strategy_evidence("available", row_count=30),
                report_phase="盤中",
            )

        unheld = unheld_message(messages)
        low_volume_card = card_block(unheld, "【光寶科 2301】")
        buyable_card = card_block(unheld, "【建準 2421】")

        self.assertIn("等量能", low_volume_card)
        self.assertIn("RR -（量能不足）", low_volume_card)
        self.assertIn("不適用（量能不足）", low_volume_card)
        self.assertNotIn("綜合 100", low_volume_card)
        self.assertNotIn("技術 93", low_volume_card)
        self.assertIn("綜合", buyable_card)

    def test_v20_4_36_failed_unheld_uses_risk_unavailable_before_heat(self):
        failed_hot = self.evidence_payload(confidence=80, decision="FAIL", action=0, rr=1.8, distance=0.5, heat="HOT")
        failed_hot["stock_code"] = "3481"
        failed_hot["result"].update({
            "structure_phase": "FAILED_BREAKOUT",
            "price_behavior": "LIMIT_LOCK",
            "market_grade": "D",
        })

        with patch.object(generator, "market_theme_summary_evidence", return_value=self.confirmed_market_evidence()):
            messages = generator.formatTelegramMessages(
                {"群創": failed_hot},
                "",
                None,
                None,
                {"trade_date": "2026-06-04"},
                datetime(2026, 6, 4),
                strategy_evidence_summary=structured_strategy_evidence("available", row_count=30),
                report_phase="盤中",
            )

        card = card_block(unheld_message(messages), "【群創 3481】")
        self.assertIn("淘汰", card)
        self.assertIn("證據：風控不適用", card)
        self.assertNotIn("證據：過熱不適用", card)

    def test_0604_v20_4_36_mobile_readability_message_list_replay(self):
        today_stop = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 94],
            {"shares": 100, "avg_price": 100},
            price=94,
            change=-6.0,
        )
        today_stop["stock_code"] = "2303"
        today_stop["position_events"] = {"event_count": 1, "bought_shares": 100, "buy_price": 100}
        today_stop["holding_decision"] = {
            "action": "停損",
            "level": "STOP_100",
            "shares": 100,
            "note": "同日建倉後跌破 hard_stop",
            "hard_stop_price": 95,
            "warning_price": 97,
        }
        today_reduce = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 96],
            {"shares": 100, "avg_price": 100},
            price=96,
            change=-4.0,
        )
        today_reduce["stock_code"] = "2408"
        today_reduce["position_events"] = {"event_count": 1, "bought_shares": 100, "buy_price": 100}
        today_reduce["holding_decision"] = {
            "action": "減碼",
            "level": "REDUCE_25",
            "shares": 25,
            "note": "同日建倉後跌破快速止損",
            "hard_stop_price": 92,
            "warning_price": 98,
        }
        today_watch = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 101],
            {"shares": 100, "avg_price": 100},
            price=101,
            change=1.0,
        )
        today_watch["stock_code"] = "2324"
        today_watch["position_events"] = {"event_count": 1, "bought_shares": 100, "buy_price": 100}
        today_watch["holding_decision"] = {
            "action": "續抱",
            "level": "NEW_POSITION_RISK_WATCH",
            "shares": 0,
            "note": "新倉風控觀察",
            "hard_stop_price": 94,
            "warning_price": 98,
        }

        low_volume = self.evidence_payload(confidence=93, decision="WAIT", action=0, rr=1.8, distance=1)
        low_volume["stock_code"] = "2301"
        low_volume["volume_ratio"] = 0.6
        low_volume["result"].update({
            "trade_state": "NO_VOLUME",
            "volume_state": "WEAK",
            "confidence_score": 93,
        })
        failed_hot = self.evidence_payload(confidence=80, decision="FAIL", action=0, rr=1.8, distance=0.5, heat="HOT")
        failed_hot["stock_code"] = "3481"
        failed_hot["result"].update({
            "structure_phase": "FAILED_BREAKOUT",
            "price_behavior": "LIMIT_LOCK",
            "market_grade": "D",
        })
        failed_gigabyte = self.evidence_payload(confidence=79, decision="FAIL", action=0, rr=1.5, distance=0.8, heat="HOT")
        failed_gigabyte["stock_code"] = "2376"
        failed_gigabyte["result"].update({
            "structure_phase": "FAILED_BREAKOUT",
            "price_behavior": "WEAK_REBOUND",
            "market_grade": "D",
        })
        buyable_weak = self.evidence_payload(confidence=82, decision="BUY", action=0.1, rr=1.8, distance=0.5)
        buyable_weak["stock_code"] = "2421"
        buyable_weak["backtest_context"] = {
            "sample": 38,
            "reference": "高",
            "win_rate": 42,
            "avg_return": -0.8,
        }
        ordinary_history = self.evidence_payload(confidence=64, decision="WAIT", action=0, rr=1.2, distance=2, heat="HOT")
        ordinary_history["stock_code"] = "9991"
        ordinary_history["cross_day_context"] = {
            "source_status": "ready",
            "source_of_truth": ["daily_signal_snapshot"],
            "previous_state": "observe",
            "previous_action": "observe",
            "repair_status": "improving",
            "consecutive_observe_days": 1,
            "historical_evidence_weight": 1,
            "weight_reason": ["修復中", "連續觀察 1 天"],
        }

        with patch.object(generator, "market_theme_summary_evidence", return_value=self.confirmed_market_evidence()):
            messages = generator.formatTelegramMessages(
                {
                    "聯電": today_stop,
                    "華邦電": today_reduce,
                    "仁寶": today_watch,
                    "光寶科": low_volume,
                    "群創": failed_hot,
                    "技嘉": failed_gigabyte,
                    "建準": buyable_weak,
                    "修復股": ordinary_history,
                },
                "FULL DETAIL",
                None,
                None,
                {"trade_date": "2026-06-04"},
                datetime(2026, 6, 4),
                strategy_evidence_summary=structured_strategy_evidence("available", row_count=30),
                report_phase="盤中",
            )

        summary = summary_message(messages)
        position = position_message(messages)
        unheld = unheld_message(messages)
        rendered = "\n\n".join(messages)
        low_volume_card = card_block(unheld, "【光寶科 2301】")
        failed_card = card_block(unheld, "【群創 3481】")
        gigabyte_card = card_block(unheld, "【技嘉 2376】")
        buyable_card = card_block(unheld, "【建準 2421】")
        history_card = card_block(unheld, "【修復股 9991】")

        self.assertIn("今日已買 3（已風控 2/觀察 1）", summary)
        self.assertNotIn("今日新建倉 3", summary)
        self.assertNotIn("資料：持倉與現價已確認；風控由持倉成本/停損推算", position)
        self.assertNotIn("資料：現價與 OHLCV 已確認；RR/分數/量能為模型推算", unheld)
        self.assertIn("等量能", low_volume_card)
        self.assertIn("RR -（量能不足）", low_volume_card)
        self.assertIn("不適用（量能不足）｜證據：量能不適用", low_volume_card)
        self.assertIn("淘汰", failed_card)
        self.assertIn("不適用（不可行動）｜證據：風控不適用", failed_card)
        self.assertNotIn("不適用（過熱）", failed_card)
        self.assertIn("淘汰", gigabyte_card)
        self.assertIn("證據：風控不適用", gigabyte_card)
        self.assertNotIn("證據：過熱不適用", gigabyte_card)
        self.assertIn("回測（建準）：樣本38｜參考度高｜3日勝率42%｜相對-0.8%｜偏弱", rendered)
        self.assertIn("回測僅輔助，分批小倉、不追價", buyable_card)
        self.assertNotIn("前次 observe", history_card)
        self.assertNotIn("修復中｜連續觀察 1 天｜權重 +1", history_card)
        self.assertIn(f"🧾 {generator.VERSION} 簡報", summary)

    def test_0604_v20_4_37_generate_mobile_consistency_message_list_replay(self):
        today_watch = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 101],
            {"shares": 100, "avg_price": 100},
            price=101,
            change=1.0,
        )
        today_watch["stock_code"] = "2324"
        today_watch["position_events"] = {"event_count": 1, "bought_shares": 100, "buy_price": 100}
        today_watch["holding_decision"] = {
            "action": "續抱",
            "level": "NEW_POSITION_RISK_WATCH",
            "shares": 0,
            "note": "新倉風控觀察",
            "hard_stop_price": 94,
            "warning_price": 98,
        }
        today_reduce = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 96],
            {"shares": 100, "avg_price": 100},
            price=96,
            change=-4.0,
        )
        today_reduce["stock_code"] = "2408"
        today_reduce["position_events"] = {"event_count": 1, "bought_shares": 100, "buy_price": 100}
        today_reduce["holding_decision"] = {
            "action": "減碼",
            "level": "REDUCE_25",
            "shares": 25,
            "note": "同日建倉後跌破快速止損",
            "hard_stop_price": 92,
            "warning_price": 98,
        }
        today_stop = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 94],
            {"shares": 100, "avg_price": 100},
            price=94,
            change=-6.0,
        )
        today_stop["stock_code"] = "2303"
        today_stop["position_events"] = {"event_count": 1, "bought_shares": 100, "buy_price": 100}
        today_stop["holding_decision"] = {
            "action": "停損",
            "level": "STOP_100",
            "shares": 100,
            "note": "同日建倉後跌破 hard_stop",
            "hard_stop_price": 95,
            "warning_price": 97,
        }

        backtest_context = {"sample": 38, "reference": "高", "win_rate": 58, "avg_return": 1.2}
        prepare = self.evidence_payload(confidence=82, decision="WAIT", action=0, rr=1.8, distance=1)
        prepare["stock_code"] = "2421"
        prepare["backtest_context"] = backtest_context

        cooldowns = {}
        for name, code in [("緯創", "3231"), ("技嘉", "2376")]:
            payload = self.evidence_payload(confidence=70, decision="WAIT", action=0, rr=1.3, distance=2, heat="HOT")
            payload["stock_code"] = code
            payload["result"]["trade_state"] = "EXTENDED"
            cooldowns[name] = payload
        cooldowns["緯創"]["backtest_context"] = dict(backtest_context)

        rr_wait = self.evidence_payload(confidence=66, decision="WAIT", action=0, rr=0.8, distance=2)
        rr_wait["stock_code"] = "2356"
        low_volume = self.evidence_payload(confidence=64, decision="WAIT", action=0, rr=1.5, distance=1)
        low_volume["stock_code"] = "2301"
        low_volume["volume_ratio"] = 0.6
        low_volume["result"].update({"trade_state": "NO_VOLUME", "volume_state": "WEAK"})
        rejected_a = self.evidence_payload(confidence=44, decision="FAIL", action=0, rr=1.2, distance=1)
        rejected_a["stock_code"] = "3481"
        rejected_a["result"].update({"structure_phase": "FAILED_BREAKOUT", "market_grade": "D"})
        rejected_b = self.evidence_payload(confidence=42, decision="FAIL", action=0, rr=1.2, distance=1)
        rejected_b["stock_code"] = "2337"
        rejected_b["result"].update({"structure_phase": "FAILED_BREAKOUT", "market_grade": "D"})
        ordinary_history = self.evidence_payload(confidence=62, decision="WAIT", action=0, rr=1.2, distance=2, heat="HOT")
        ordinary_history["stock_code"] = "9991"
        ordinary_history["cross_day_context"] = {
            "source_status": "ready",
            "source_of_truth": ["daily_signal_snapshot"],
            "previous_state": "observe",
            "previous_action": "observe",
            "repair_status": "improving",
            "consecutive_observe_days": 1,
            "historical_evidence_weight": 1,
            "weight_reason": ["修復中", "連續觀察 1 天"],
        }

        with patch.object(generator, "market_theme_summary_evidence", return_value=self.confirmed_market_evidence()):
            messages = generator.formatTelegramMessages(
                {
                    "聯電": today_stop,
                    "華邦電": today_reduce,
                    "仁寶": today_watch,
                    "建準": prepare,
                    **cooldowns,
                    "仁寶候選": rr_wait,
                    "光寶科": low_volume,
                    "群創": rejected_a,
                    "旺宏": rejected_b,
                    "修復股": ordinary_history,
                },
                "FULL DETAIL",
                None,
                None,
                {"trade_date": "2026-06-04"},
                datetime(2026, 6, 4),
                strategy_evidence_summary=structured_strategy_evidence("available", row_count=30),
                report_phase="盤中",
            )

        summary = summary_message(messages)
        unheld = unheld_message(messages)
        rendered = "\n\n".join(messages)
        first_market_line = first_line_for_prefix(summary, "市場：")

        self.assertIn("【06/04 盤中｜v20.4.47】", summary)
        self.assertIn("今日已買 3（已風控 2/觀察 1）", first_market_line)
        self.assertNotIn("風控中", first_market_line)
        self.assertIn("未持倉 8（不可追高觀察1/僅追蹤5/淘汰2）", first_market_line)
        self.assertIn("未持倉 8｜不可追高觀察 1（不可買）｜僅追蹤 5", summary)
        self.assertIn("淘汰 2", summary)
        self.assertIn("📎 詳情索引：持倉 聯電、華邦電、仁寶｜交易執行 2｜不可追高觀察 1｜僅追蹤 5｜淘汰 2", summary)
        self.assertIn("【建準 2421】👀 不可追高觀察", unheld)
        self.assertNotIn("修復中｜連續觀察 1 天｜權重 +1", card_block(unheld, "【修復股 9991】"))
        self.assertIn("回測（建準）：樣本38｜參考度高｜3日勝率58%｜相對+1.2%｜略優", rendered)
        self.assertNotIn("回測（緯創）：樣本38｜參考度高｜3日勝率58%｜相對+1.2%｜略優", summary)
        self.assertNotIn("回測（建準、緯創）", rendered)

    def test_v20_4_36_unheld_funnel_hides_zero_count_buckets(self):
        cooldown = self.evidence_payload(confidence=70, decision="WAIT", action=0, rr=1.2, distance=2, heat="HOT")
        cooldown["result"]["trade_state"] = "EXTENDED"
        low_volume = self.evidence_payload(confidence=70, decision="WAIT", action=0, rr=1.4, distance=1)
        low_volume["result"].update({"trade_state": "NO_VOLUME", "volume_state": "WEAK"})
        rejected = self.evidence_payload(confidence=40, decision="FAIL", action=0, rr=1.4, distance=1)
        rejected["result"].update({"structure_phase": "FAILED_BREAKOUT", "market_grade": "D"})

        text = generator.format_unheld_funnel([
            ("冷卻", cooldown),
            ("量能", low_volume),
            ("淘汰", rejected),
        ])

        self.assertIn("未持倉 3", text)
        self.assertIn("僅追蹤 2", text)
        self.assertIn("等冷卻1/等量能1", text)
        self.assertIn("淘汰 1", text)
        self.assertNotIn("可買 0", text)
        self.assertNotIn("不可追高觀察 0", text)

    def test_v20_4_37_single_backtest_lines_are_not_aggregated(self):
        payload = self.evidence_payload(confidence=80)
        payload["backtest_context"] = {"sample": 38, "win_rate": 58, "avg_return": 1.2}
        same_payload = self.evidence_payload(confidence=78)
        same_payload["backtest_context"] = {"sample": 38, "win_rate": 58, "avg_return": 1.2}
        context = {
            "evidence_manifest": [
                {"field_name": "evidence.strategy_sample", "source_status": "available"},
            ],
        }

        lines = generator.format_backtest_groups([("建準", payload), ("緯創", same_payload)], report_context=context)

        self.assertEqual(lines, [
            "",
            "回測摘要",
            "回測（建準）：樣本38｜參考度高｜3日勝率58%｜相對+1.2%｜略優",
            "回測（緯創）：樣本38｜參考度高｜3日勝率58%｜相對+1.2%｜略優",
        ])
        self.assertNotIn("回測（建準、緯創）", "\n".join(lines))

    def confirmed_market_evidence(
        self,
        trend_status="confirmed_trend",
        observed_days=20,
        recent_supporting_days=5,
        support_streak_days=3,
    ):
        return {
            "confirmed": True,
            "source_status": "ready",
            "theme_status": "confirmed",
            "level": "confirmed",
            "theme": "AI",
            "evidence_trend": {
                "status": trend_status,
                "observed_days": observed_days,
                "recent_supporting_days": recent_supporting_days,
                "support_streak_days": support_streak_days,
            },
        }

    def missing_market_evidence(self):
        return {
            "confirmed": False,
            "source_status": "missing-source",
            "theme_status": "absent",
            "level": "absent",
            "evidence_trend": {},
        }

    def confirmed_strategy_evidence(self):
        return {
            "source_status": "available",
            "sample": 30,
            "win_rate": 70,
            "avg_return": 2.0,
            "label": "confirmed",
        }

    def test_report_score_evidence_display_owner_specimen_message_list_replay(self):
        holding_non_add = self.evidence_payload(confidence=96, decision="BUY", action=0.1, rr=2.7, distance=0.2)
        holding_non_add.update({
            "stock_code": "2421",
            "holding": {"shares": 50, "avg_price": 90},
            "market_theme_evidence": self.confirmed_market_evidence(),
            "strategy_sample_evidence": self.confirmed_strategy_evidence(),
            "holding_decision": {
                "action": "暫不加碼",
                "level": "HOLD",
                "note": "新倉風控觀察，暫不加碼",
                "allow_add": False,
                "warning_price": 95,
                "hard_stop_price": 90,
            },
        })
        holding_add = self.evidence_payload(confidence=90, decision="BUY", action=0.1, rr=2.2, distance=0.4)
        holding_add.update({
            "stock_code": "3035",
            "holding": {"shares": 20, "avg_price": 88},
            "market_theme_evidence": self.confirmed_market_evidence(),
            "strategy_sample_evidence": self.confirmed_strategy_evidence(),
            "holding_decision": {
                "action": "加碼 10%",
                "level": "ADD_10",
                "note": "加碼條件成立",
                "allow_add": True,
                "warning_price": 95,
                "hard_stop_price": 90,
            },
        })
        over_cap = self.evidence_payload(confidence=96, decision="BUY", action=0.1, rr=2.4, distance=0.3)
        over_cap["stock_code"] = "2301"
        over_cap["market_theme_evidence"] = self.confirmed_market_evidence()
        over_cap["strategy_sample_evidence"] = self.confirmed_strategy_evidence()
        overheat = self.evidence_payload(confidence=80, decision="WAIT", action=0, rr=1.5, distance=1.0, heat="HOT")
        overheat["stock_code"] = "2376"
        overheat["market_theme_evidence"] = self.confirmed_market_evidence()
        overheat["strategy_sample_evidence"] = self.confirmed_strategy_evidence()
        risk_blocked = self.evidence_payload(confidence=72, decision="FAIL", action=0, rr=1.5, distance=1.0)
        risk_blocked["stock_code"] = "2344"
        risk_blocked["result"]["structure_phase"] = "FAILED_BREAKOUT"
        risk_blocked["market_theme_evidence"] = self.confirmed_market_evidence()
        risk_blocked["strategy_sample_evidence"] = self.confirmed_strategy_evidence()
        missing_data = self.evidence_payload(confidence=55, decision="WAIT", action=0, rr=1.1, distance=1.5)
        missing_data["stock_code"] = "0001"
        low_volume = self.evidence_payload(confidence=82, decision="WAIT", action=0, rr=1.2, distance=1.5)
        low_volume["stock_code"] = "0002"
        low_volume["volume_ratio"] = 0.7
        low_volume["result"].update({
            "structure_phase": "BASE",
            "volume_price_state": "COILING",
            "market_grade": "A",
        })
        low_volume["market_theme_evidence"] = self.confirmed_market_evidence()
        low_volume["strategy_sample_evidence"] = self.confirmed_strategy_evidence()
        low_score_flat = self.evidence_payload(confidence=7, decision="WAIT", action=0, rr=1.2, distance=1.5)
        low_score_flat["stock_code"] = "0003"
        low_score_flat["market_theme_evidence"] = self.confirmed_market_evidence()
        low_score_flat["strategy_sample_evidence"] = self.confirmed_strategy_evidence()

        results = {
            "建準": holding_non_add,
            "加碼股": holding_add,
            "新倉候選": over_cap,
            "過熱股": overheat,
            "風控股": risk_blocked,
            "缺資料": missing_data,
            "低量標的": low_volume,
            "低分股": low_score_flat,
        }
        with patch.object(generator, "market_theme_summary_evidence", return_value=self.missing_market_evidence()):
            messages = generator.formatTelegramMessages(
                results,
                "",
                None,
                None,
                {"trade_date": "2026-06-03"},
                datetime(2026, 6, 3),
                strategy_evidence_summary=structured_strategy_evidence("available", row_count=30),
                report_phase="盤後",
            )

        rendered = "\n\n".join(messages)
        holding = position_message(messages)
        unheld = unheld_message(messages)
        non_add_card = card_block(holding, "【建準 2421】")
        add_card = card_block(holding, "【加碼股 3035】")
        over_cap_card = card_block(unheld, "【新倉候選 2301】")
        overheat_card = card_block(unheld, "【過熱股 2376】")
        risk_card = card_block(unheld, "【風控股 2344】")
        missing_card = card_block(unheld, "【缺資料 0001】")
        low_volume_card = card_block(unheld, "【低量標的 0002】")
        low_score_card = card_block(unheld, "【低分股 0003】")

        self.assertIn("【06/03 盤後｜v20.4.47】", rendered)
        self.assertIn("數據：不適用（既有持倉）｜V 1.4x", non_add_card)
        self.assertNotIn("綜合", non_add_card)
        self.assertNotIn("技術", non_add_card)
        self.assertNotIn("證據", non_add_card)
        self.assertNotIn("RR 2.7", non_add_card)
        self.assertIn("綜合", add_card)
        self.assertIn("綜合 100｜技術 96", over_cap_card)
        self.assertNotRegex(rendered, r"綜合 10[1-9]")
        self.assertIn("證據：過熱不適用", overheat_card)
        self.assertIn("證據：風控不適用", risk_card)
        self.assertIn("證據：資料不足", missing_card)
        self.assertNotIn("極強", low_volume_card)
        self.assertIn("縮量觀察", low_volume_card)
        self.assertNotIn("突破確認｜待確認", low_volume_card)
        self.assertIn("綜合 8｜技術 7｜證據：微幅（confirmed）", low_score_card)
        self.assertNotIn("證據 +", low_score_card)

    def test_evidence_score_missing_keeps_technical_confidence_and_no_adjustment(self):
        payload = self.evidence_payload(confidence=80)
        with patch.object(generator, "market_theme_summary_evidence", return_value=self.missing_market_evidence()):
            context = generator.build_report_context(
                {"缺證據": payload},
                {"trade_date": "2026-06-02"},
                datetime(2026, 6, 2),
                strategy_evidence_summary=structured_strategy_evidence("insufficient-data", row_count=0),
                report_phase="盤中",
            )

        result = payload["result"]
        self.assertEqual(generator.compute_evidence_score(context, "缺證據"), (None, "unavailable"))
        self.assertEqual(result["evidence_modifier"], 1.0)
        self.assertEqual(result["final_confidence"], result["technical_confidence"])
        self.assertEqual(generator.unheld_funnel_state("缺證據", payload, report_context=context), "可準備")
        self.assertIsNone(payload.get("evidence_adjustment_reason"))

    def test_per_stock_evidence_uses_stock_theme_and_setup_not_report_level_shared_score(self):
        stock_a = self.evidence_payload(confidence=74)
        stock_a["market_theme_evidence"] = self.confirmed_market_evidence()
        stock_a["strategy_sample_evidence"] = {
            "sample": 18,
            "win_rate": 66,
            "avg_return": 1.6,
            "label": "confirmed",
        }
        stock_b = self.evidence_payload(confidence=74)
        stock_b["market_theme_evidence"] = {
            "source_status": "insufficient-data",
            "label": "supporting",
            "evidence_trend": {
                "status": "supporting_trend",
                "observed_days": 1,
                "recent_supporting_days": 1,
                "support_streak_days": 0,
            },
        }
        stock_b["strategy_sample_evidence"] = {
            "sample": 18,
            "win_rate": 48,
            "avg_return": 0.2,
            "label": "supporting",
        }
        with patch.object(generator, "market_theme_summary_evidence", return_value=self.confirmed_market_evidence()):
            context = generator.build_report_context(
                {"A": stock_a, "B": stock_b},
                {"trade_date": "2026-06-02"},
                datetime(2026, 6, 2),
                strategy_evidence_summary=structured_strategy_evidence("available", row_count=30),
                report_phase="盤中",
            )

        score_a, status_a = generator.compute_evidence_score(context, "A")
        score_b, status_b = generator.compute_evidence_score(context, "B")
        result_a = stock_a["result"]
        result_b = stock_b["result"]
        fields = {field["field_name"]: field for field in context["evidence_manifest"]}

        self.assertEqual(status_a, "confirmed")
        self.assertEqual(status_b, "supporting")
        self.assertGreater(score_a, score_b)
        self.assertNotEqual(result_a["evidence_score"], result_b["evidence_score"])
        self.assertNotEqual(result_a["evidence_modifier"], result_b["evidence_modifier"])
        self.assertNotEqual(result_a["final_confidence"], result_b["final_confidence"])
        self.assertEqual(result_a["evidence_modifier"], 1.15)
        self.assertLessEqual(result_b["evidence_modifier"], 1.08)
        self.assertEqual(fields["stock.A.score"]["value"]["evidence_status"], "confirmed")
        self.assertEqual(fields["stock.B.score"]["value"]["evidence_status"], "supporting")

    def test_market_theme_source_error_supporting_payload_fails_closed_before_supporting(self):
        context = {
            "evidence_manifest": [
                {"field_name": "evidence.market_theme", "source_status": "source-error"},
            ],
            "per_stock_evidence": {
                "B": {
                    "market_theme": {
                        "source_status": "source-error",
                        "trend": "up",
                        "label": "supporting",
                        "level": "supporting",
                        "observed": 5,
                        "streak": 5,
                    }
                }
            },
        }

        payload = generator._market_theme_evidence_payload(context, "B")

        self.assertEqual(payload["status"], "unavailable")
        self.assertIsNone(payload["score"])
        self.assertFalse(payload["decision_eligible"])

    def test_eight_day_confirmed_market_theme_is_decision_eligible(self):
        context = {
            "market_theme_evidence": self.confirmed_market_evidence(
                observed_days=8,
                recent_supporting_days=3,
                support_streak_days=3,
            ),
            "evidence_manifest": [
                {"field_name": "evidence.market_theme", "source_status": "available"},
            ],
        }

        market = generator._market_theme_evidence_payload(context)

        self.assertEqual(generator.VERSION, "v20.4.47")
        self.assertEqual(market["status"], "confirmed")
        self.assertEqual(market["score"], 1.0)
        self.assertTrue(market["decision_eligible"])

    def test_strategy_sample_count_accepts_classification_sample_count(self):
        context = {
            "evidence_manifest": [
                {"field_name": "evidence.strategy_sample", "source_status": "available"},
            ],
            "strategy_evidence_summary": {
                "classification_sample_count": 36,
            },
            "strategy_sample_structured_status": {
                "status": "available",
                "source": "daily_signal_snapshot",
                "sample": 36,
            },
        }

        status, reason = generator._strategy_sample_status({
            "structured_status": {
                "status": "available",
                "source": "daily_signal_snapshot",
                "classification_sample_count": 36,
                "missing_fields": [],
                "completeness": "complete",
            },
        })
        payload = generator._strategy_sample_evidence_payload(context)

        self.assertEqual(status, "available")
        self.assertIn("daily_signal_snapshot", reason)
        self.assertEqual(generator._strategy_sample_row_count(context), 36)
        self.assertEqual(payload["status"], "ready")
        self.assertEqual(payload["score"], 1.0)
        self.assertEqual(payload["sample"], 36)
        self.assertTrue(payload["decision_eligible"])

    def test_per_stock_backtest_context_drives_strategy_ready_when_global_sample_partial(self):
        wistron = self.evidence_payload(confidence=78, decision="BUY", action=0.1, rr=1.6, distance=0.5)
        wistron["stock_code"] = "3231"
        wistron["backtest_context"] = {
            "sample": 36,
            "reference": "高",
            "win_rate": 58,
            "avg_return": 1.2,
        }
        winbond = self.evidence_payload(confidence=76, decision="WAIT", action=0, rr=1.4, distance=2)
        winbond["stock_code"] = "2344"
        winbond["backtest_context"] = {
            "sample": 38,
            "reference": "高",
            "win_rate": 56,
            "avg_return": 1.1,
            "mfe_mae_score": 0.6,
        }
        low_sample = self.evidence_payload(confidence=70, decision="WAIT", action=0, rr=1.3, distance=2)
        low_sample["backtest_context"] = {"sample": 9, "reference": "高", "win_rate": 70, "avg_return": 2.0}
        no_history = self.evidence_payload(confidence=69, decision="WAIT", action=0, rr=1.2, distance=2)
        no_history["backtest_context"] = None
        weak = self.evidence_payload(confidence=74, decision="FAIL", action=0, rr=1.7, distance=0.5)
        weak["stock_code"] = "2303"
        weak["result"].update({
            "structure_phase": "FAILED_BREAKOUT",
            "market_grade": "D",
            "entry_quality": "D",
        })
        weak["backtest_context"] = {"sample": 36, "reference": "高", "win_rate": 60, "avg_return": 1.5}

        with patch.object(generator, "market_theme_summary_evidence", return_value=self.missing_market_evidence()):
            messages = generator.formatTelegramMessages(
                {
                    "緯創": wistron,
                    "華邦": winbond,
                    "低樣本": low_sample,
                    "無歷史": no_history,
                    "聯電": weak,
                },
                "FULL DETAIL",
                None,
                None,
                {"trade_date": "2026-06-03"},
                datetime(2026, 6, 3),
                strategy_evidence_summary=structured_strategy_evidence("available", row_count=3),
                report_phase="盤中",
            )
            context = generator.build_report_context(
                {
                    "緯創": wistron,
                    "華邦": winbond,
                    "低樣本": low_sample,
                    "無歷史": no_history,
                    "聯電": weak,
                },
                {"trade_date": "2026-06-03"},
                datetime(2026, 6, 3),
                strategy_evidence_summary=structured_strategy_evidence("available", row_count=3),
                report_phase="盤中",
            )

        self.assertEqual(generator._per_stock_strategy_sample_evidence_payload(context, "緯創")["status"], "ready")
        self.assertEqual(generator._per_stock_strategy_sample_evidence_payload(context, "緯創")["sample"], 36)
        self.assertEqual(generator._per_stock_strategy_sample_evidence_payload(context, "華邦")["status"], "ready")
        self.assertEqual(generator._per_stock_strategy_sample_evidence_payload(context, "華邦")["sample"], 38)
        self.assertEqual(generator._per_stock_strategy_sample_evidence_payload(context, "低樣本")["status"], "partial")
        self.assertEqual(generator._per_stock_strategy_sample_evidence_payload(context, "無歷史")["status"], "unavailable")
        self.assertGreater(wistron["result"]["evidence_modifier"], 1.0)
        self.assertGreater(winbond["result"]["evidence_modifier"], 1.0)
        self.assertNotEqual(wistron["result"]["evidence_modifier"], winbond["result"]["evidence_modifier"])
        self.assertNotEqual(wistron["result"]["final_confidence"], wistron["result"]["technical_confidence"])
        self.assertNotEqual(winbond["result"]["final_confidence"], winbond["result"]["technical_confidence"])
        self.assertLessEqual(weak["result"]["evidence_modifier"], 1.0)
        rendered = "\n\n".join(messages)
        self.assertIn("【06/03 盤中｜v20.4.47】", rendered)
        self.assertIn("【緯創 3231】", rendered)
        self.assertIn("綜合 84｜技術 78｜證據 +8%（supporting）", rendered)
        self.assertIn("回測（緯創）：樣本36｜參考度高｜3日勝率58%｜相對+1.2%｜略優", rendered)
        self.assertIn("【華邦 2344】", rendered)
        self.assertIn("證據 +", rendered)
        self.assertNotIn("證據：partial｜僅輔助參考", card_block(unheld_message(messages), "【緯創 3231】"))

    def test_per_stock_market_theme_missing_fallbacks_to_report_level_confirmed(self):
        context = {
            "market_theme_evidence": self.confirmed_market_evidence(),
            "per_stock_evidence": {
                "A": {
                    "market_theme": self.confirmed_market_evidence(),
                    "strategy_sample": {
                        "source_status": "available",
                        "sample": 20,
                        "win_rate": 70,
                        "avg_return": 2.0,
                        "label": "confirmed",
                    },
                },
                "B": {},
            },
        }

        market_a = generator._market_theme_evidence_payload(context, "A")
        market_b = generator._market_theme_evidence_payload(context, "B")
        score_a, status_a = generator.compute_evidence_score(context, "A")
        score_b, status_b = generator.compute_evidence_score(context, "B")

        self.assertEqual(market_a["status"], "confirmed")
        self.assertEqual(market_a["score"], 1.0)
        self.assertGreater(score_a, 0)
        self.assertEqual(status_a, "confirmed")
        self.assertEqual(market_b["status"], "confirmed")
        self.assertEqual(market_b["score"], 1.0)
        self.assertTrue(market_b["decision_eligible"])
        self.assertEqual((score_b, status_b), (1.0, "supporting"))
        self.assertGreater(generator.evidence_modifier_for_score(score_b, status_b), 1.0)

    def test_per_stock_strategy_sample_missing_does_not_fallback_to_report_level_ready(self):
        context = {
            "evidence_manifest": [
                {"field_name": "evidence.strategy_sample", "source_status": "available", "value": "樣本 30"},
                {"field_name": "evidence.market_theme", "source_status": "missing-source"},
            ],
            "strategy_sample_structured_status": structured_strategy_evidence("available", row_count=30),
            "per_stock_evidence": {
                "B": {},
            },
        }

        strategy_payload = generator._per_stock_strategy_sample_evidence_payload(context, "B")
        score, status = generator.compute_evidence_score(context, "B")

        self.assertEqual(strategy_payload["status"], "unavailable")
        self.assertIsNone(strategy_payload["score"])
        self.assertFalse(strategy_payload["decision_eligible"])
        self.assertEqual((score, status), (None, "unavailable"))
        self.assertEqual(generator.evidence_modifier_for_score(score, status), 1.0)

    def test_per_stock_strategy_sample_status_does_not_depend_on_report_level_manifest(self):
        context = {
            "evidence_manifest": [
                {"field_name": "evidence.strategy_sample", "source_status": "missing-source"},
                {"field_name": "evidence.market_theme", "source_status": "missing-source"},
            ],
            "per_stock_evidence": {
                "A": {
                    "strategy_sample": {
                        "source_status": "available",
                        "sample": 20,
                        "win_rate": 70,
                        "avg_return": 2.0,
                        "label": "confirmed",
                    }
                }
            },
        }

        strategy_payload = generator._per_stock_strategy_sample_evidence_payload(context, "A")
        score, status = generator.compute_evidence_score(context, "A")

        self.assertEqual(strategy_payload["status"], "ready")
        self.assertEqual(strategy_payload["score"], 1.0)
        self.assertEqual(strategy_payload["sample"], 20)
        self.assertTrue(strategy_payload["decision_eligible"])
        self.assertIsNotNone(score)
        self.assertNotEqual(status, "unavailable")
        self.assertEqual(status, "supporting")

    def test_setup_strategy_summary_drives_per_stock_modifier_and_rendered_cards(self):
        breakout = self.evidence_payload(confidence=68, decision="WAIT", action=0, rr=1.4, distance=2)
        breakout["result"]["watch_category"] = "突破確認"
        failed = self.evidence_payload(confidence=0, decision="FAIL", action=0, rr=0, distance=9)
        failed["result"]["structure_phase"] = "FAILED_BREAKOUT"
        failed["result"]["market_grade"] = "D"
        failed["result"]["reject_family"] = "突破失敗"
        summary = structured_strategy_evidence("available", row_count=22)
        summary["setup_strategy_samples"] = {
            "突破確認": {
                "setup_key": "突破確認",
                "source_status": "available",
                "status": "ready",
                "sample_count": 12,
                "win_rate": 67,
                "mfe_mae_score": 0.70,
            },
            "突破失敗": {
                "setup_key": "突破失敗",
                "source_status": "available",
                "status": "ready",
                "sample_count": 10,
                "win_rate": 30,
                "mfe_mae_score": 0.35,
            },
        }

        with patch.object(generator, "market_theme_summary_evidence", return_value=self.confirmed_market_evidence("supporting_trend")):
            messages = generator.formatTelegramMessages(
                {"旺宏": breakout, "聯電": failed},
                "",
                None,
                None,
                {"trade_date": "2026-06-02"},
                datetime(2026, 6, 2),
                strategy_evidence_summary=summary,
                report_phase="盤中",
            )
            context = generator.build_report_context(
                {"旺宏": breakout, "聯電": failed},
                {"trade_date": "2026-06-02"},
                datetime(2026, 6, 2),
                strategy_evidence_summary=summary,
                report_phase="盤中",
            )
        macronix_score, macronix_status = generator.compute_evidence_score(context, "旺宏")
        umc_score, umc_status = generator.compute_evidence_score(context, "聯電")
        rendered = "\n\n".join(messages)
        macronix_card = card_block(unheld_message(messages), "【旺宏")
        umc_card = card_block(unheld_message(messages), "【聯電")

        self.assertNotEqual(macronix_score, umc_score)
        self.assertNotEqual(breakout["result"]["evidence_modifier"], failed["result"]["evidence_modifier"])
        self.assertGreater(breakout["result"]["evidence_modifier"], 1.0)
        self.assertEqual(failed["result"]["evidence_modifier"], 1.0)
        self.assertIn(macronix_status, {"supporting", "partial"})
        self.assertIn(umc_status, {"supporting", "neutral", "partial"})
        self.assertEqual(failed["result"]["evidence_status"], "unavailable")
        self.assertIn("證據 +", macronix_card)
        self.assertIn("證據：風控不適用", umc_card)
        self.assertNotIn("證據 +", umc_card)

    def test_setup_summary_without_explicit_stock_setup_fails_closed_and_hides_boost(self):
        inferred_only = self.evidence_payload(confidence=68, decision="WAIT", action=0, rr=1.4, distance=2)
        summary = structured_strategy_evidence("available", row_count=12)
        summary["setup_strategy_samples"] = {
            "突破確認": {
                "setup_key": "突破確認",
                "source_status": "available",
                "status": "ready",
                "sample_count": 12,
                "win_rate": 70,
                "mfe_mae_score": 0.75,
            }
        }

        with patch.object(generator, "market_theme_summary_evidence", return_value=self.missing_market_evidence()):
            messages = generator.formatTelegramMessages(
                {"缺明確setup": inferred_only},
                "",
                None,
                None,
                {"trade_date": "2026-06-02"},
                datetime(2026, 6, 2),
                strategy_evidence_summary=summary,
                report_phase="盤中",
            )
            context = generator.build_report_context(
                {"缺明確setup": inferred_only},
                {"trade_date": "2026-06-02"},
                datetime(2026, 6, 2),
                strategy_evidence_summary=summary,
                report_phase="盤中",
            )
        strategy_payload = generator._per_stock_strategy_sample_evidence_payload(context, "缺明確setup")
        score, status = generator.compute_evidence_score(context, "缺明確setup")
        card = card_block(unheld_message(messages), "【缺明確setup")

        self.assertEqual(strategy_payload["status"], "unavailable")
        self.assertIsNone(strategy_payload["score"])
        self.assertEqual((score, status), (None, "unavailable"))
        self.assertEqual(inferred_only["result"]["evidence_modifier"], 1.0)
        self.assertIn("證據：資料不足", card)
        self.assertNotIn("證據 +", card)

    def test_supporting_evidence_modifier_is_capped_below_ceiling(self):
        self.assertLessEqual(generator.evidence_modifier_for_score(1.0, "supporting"), 1.08)
        self.assertLess(generator.evidence_modifier_for_score(1.0, "supporting"), 1.15)
        self.assertEqual(generator.evidence_modifier_for_score(1.0, "confirmed"), 1.15)

    def test_confirmed_evidence_no_technical_setup_does_not_become_buy_or_prepare(self):
        payload = self.evidence_payload(confidence=70, decision="WAIT", action=0, distance=9)
        payload["market_theme_evidence"] = self.confirmed_market_evidence()
        payload["strategy_sample_evidence"] = self.confirmed_strategy_evidence()
        payload["result"]["structure_phase"] = "BASE"
        payload["result"]["price_behavior"] = "NORMAL"
        with patch.object(generator, "market_theme_summary_evidence", return_value=self.confirmed_market_evidence()):
            context = generator.build_report_context(
                {"無setup": payload},
                {"trade_date": "2026-06-02"},
                datetime(2026, 6, 2),
                strategy_evidence_summary=structured_strategy_evidence("available", row_count=30),
                report_phase="盤中",
            )

        self.assertEqual(generator.compute_evidence_score(context, "無setup")[1], "confirmed")
        self.assertNotEqual(generator.unheld_funnel_state("無setup", payload, report_context=context), "可買")
        self.assertNotEqual(generator.unheld_funnel_state("無setup", payload, report_context=context), "可準備")
        self.assertIsNone(payload.get("evidence_adjustment_reason"))
        self.assertEqual(context["evidence"]["market_theme"]["forbidden_effects"], generator.EVIDENCE_FORBIDDEN_EFFECTS)

    def test_confirmed_evidence_near_boundary_adjusts_prepare_and_report_reason(self):
        payload = self.evidence_payload(confidence=78, decision="WAIT", action=0, rr=1.4, distance=2)
        payload["market_theme_evidence"] = self.confirmed_market_evidence()
        payload["strategy_sample_evidence"] = self.confirmed_strategy_evidence()
        with patch.object(generator, "market_theme_summary_evidence", return_value=self.confirmed_market_evidence()):
            messages = generator.formatTelegramMessages(
                {"近門檻": payload},
                "",
                None,
                None,
                {"trade_date": "2026-06-02"},
                datetime(2026, 6, 2),
                strategy_evidence_summary=structured_strategy_evidence("available", row_count=30),
                report_phase="盤中",
            )

        artifact_payload = self.evidence_payload(confidence=78, decision="WAIT", action=0, rr=1.4, distance=2)
        artifact_payload["market_theme_evidence"] = self.confirmed_market_evidence()
        artifact_payload["strategy_sample_evidence"] = self.confirmed_strategy_evidence()
        with patch.object(generator, "market_theme_summary_evidence", return_value=self.confirmed_market_evidence()):
            context = generator.build_report_context(
                {"近門檻": artifact_payload},
                {"trade_date": "2026-06-02"},
                datetime(2026, 6, 2),
                strategy_evidence_summary=structured_strategy_evidence("available", row_count=30),
                report_phase="盤中",
            )

        result = payload["result"]
        summary = summary_message(messages)
        rendered = "\n\n".join(messages)
        card = card_block(unheld_message(messages), "【近門檻")
        fields = {field["field_name"]: field for field in context["evidence_manifest"]}
        risk_value = fields["stock.近門檻.risk"]["value"]
        manifest_mentions_adjustment_reason = (
            "證據僅調整邊界，不放寬RR/過熱限制"
            in str(risk_value.get("evidence_adjustment_reason"))
        )
        self.assertEqual(generator.unheld_funnel_state("近門檻", payload, report_context={
            "evidence": {
                "market_theme": {"score": 1.0, "decision_eligible": True},
                "strategy_sample": {"score": 1.0, "decision_eligible": True},
            },
            "evidence_manifest": [],
        }), "可準備")
        self.assertLessEqual(result["evidence_modifier"], 1.15)
        self.assertIn("未持倉 1 檔可準備", summary)
        self.assertIn("可準備 1（不可買）", summary)
        self.assertIn("未持倉 1 檔可準備，等觸發，不列入今日盤中交易執行", summary)
        self.assertIn("📎 詳情索引：持倉 無｜可準備 1", summary)
        self.assertIn("【近門檻 9999】👀 可準備｜突破回測", card)
        self.assertIn("綜合 90｜技術 78｜證據 +15%（confirmed）", card)
        self.assertIn("證據僅調整邊界，不放寬RR/過熱限制", card)
        self.assertEqual(risk_value["funnel_state"], "可準備")
        self.assertTrue(manifest_mentions_adjustment_reason)
        self.assertNotIn("不可追高觀察 1", rendered)
        self.assertNotIn("【近門檻 9999】👀 待回測", rendered)
        self.assertNotIn("可買｜建議", unheld_message(messages))

    def test_official_replay_confirmed_market_and_classification_sample_changes_composite(self):
        payload = self.evidence_payload(confidence=78, decision="WAIT", action=0, rr=1.4, distance=2)
        payload["market_theme_evidence"] = self.confirmed_market_evidence(
            observed_days=8,
            recent_supporting_days=3,
            support_streak_days=3,
        )
        payload["strategy_sample_evidence"] = {
            "source_status": "available",
            "classification_sample_count": 36,
            "win_rate": 70,
            "avg_return": 2.0,
            "label": "confirmed",
        }
        strategy_summary = {
            "rendered_text": "策略樣本：來源可驗證｜樣本 36",
            "structured_status": {
                "status": "available",
                "source": "daily_signal_snapshot",
                "classification_sample_count": 36,
                "missing_fields": [],
                "completeness": "complete",
            },
            "classification_sample_count": 36,
        }

        with patch.object(generator, "market_theme_summary_evidence", return_value=self.confirmed_market_evidence(
            observed_days=8,
            recent_supporting_days=3,
            support_streak_days=3,
        )):
            messages = generator.formatTelegramMessages(
                {"建準": payload},
                "",
                None,
                None,
                {"trade_date": "2026-06-02"},
                datetime(2026, 6, 2),
                strategy_evidence_summary=strategy_summary,
                report_phase="盤中",
            )

        card = card_block(unheld_message(messages), "【建準")
        result = payload["result"]

        self.assertEqual(result["evidence_status"], "confirmed")
        self.assertGreater(result["evidence_modifier"], 1.0)
        self.assertNotEqual(round(result["final_confidence"]), round(result["technical_confidence"]))
        self.assertIn("綜合 90｜技術 78｜證據 +15%（confirmed）", card)
        self.assertNotIn("證據：partial", card)
        self.assertNotIn("證據 +0%", card)

    def test_mixed_evidence_adjusted_and_ordinary_prepare_split_counts_and_labels(self):
        adjusted = self.evidence_payload(confidence=78, decision="WAIT", action=0, rr=1.4, distance=2)
        adjusted["market_theme_evidence"] = self.confirmed_market_evidence()
        adjusted["strategy_sample_evidence"] = self.confirmed_strategy_evidence()
        ordinary = self.evidence_payload(confidence=82, decision="WAIT", action=0, rr=1.4, distance=9)
        ordinary["market_theme_evidence"] = self.confirmed_market_evidence()
        ordinary["strategy_sample_evidence"] = self.confirmed_strategy_evidence()
        ordinary["result"]["structure_phase"] = "BASE"
        ordinary["result"]["price_behavior"] = "NORMAL"
        ordinary["cross_day_context"] = {
            "source_status": "ready",
            "source_of_truth": ["position_events"],
            "previous_state": "eliminated",
            "repair_status": "repaired",
            "historical_evidence_weight": 1,
        }
        payloads = {
            "證據調整": adjusted,
            "普通準備": ordinary,
        }
        with patch.object(generator, "market_theme_summary_evidence", return_value=self.confirmed_market_evidence()):
            messages = generator.formatTelegramMessages(
                payloads,
                "",
                None,
                None,
                {"trade_date": "2026-06-02"},
                datetime(2026, 6, 2),
                strategy_evidence_summary=structured_strategy_evidence("available", row_count=30),
                report_phase="盤中",
            )

        with patch.object(generator, "market_theme_summary_evidence", return_value=self.confirmed_market_evidence()):
            context = generator.build_report_context(
                payloads,
                {"trade_date": "2026-06-02"},
                datetime(2026, 6, 2),
                strategy_evidence_summary=structured_strategy_evidence("available", row_count=30),
                report_phase="盤中",
            )

        summary = summary_message(messages)
        rendered = "\n\n".join(messages)
        unheld = unheld_message(messages)
        adjusted_card = card_block(unheld, "【證據調整")
        ordinary_card = card_block(unheld, "【普通準備")
        fields = {field["field_name"]: field for field in context["evidence_manifest"]}
        adjusted_risk = fields["stock.證據調整.risk"]["value"]
        ordinary_risk = fields["stock.普通準備.risk"]["value"]

        self.assertIn("未持倉 2｜可買 0｜可準備 1（不可買）｜不可追高觀察 1（不可買）｜淘汰 0", summary)
        self.assertIn("可準備 1（不可買）｜不可追高觀察 1（不可買）", summary)
        self.assertIn("📎 詳情索引：持倉 無｜可準備 1｜不可追高觀察 1", summary)
        self.assertNotIn("未持倉 2 檔可準備", summary)
        self.assertNotIn("可準備 2（不可買）", summary)
        self.assertIn("【證據調整 9999】👀 可準備｜突破回測", adjusted_card)
        self.assertIn("證據僅調整邊界，不放寬RR/過熱限制", adjusted_card)
        self.assertIn("【普通準備 9999】👀 不可追高觀察", ordinary_card)
        self.assertNotIn("【普通準備 9999】👀 待回測", ordinary_card)
        self.assertNotIn("證據僅調整邊界，不放寬RR/過熱限制", ordinary_card)
        self.assertEqual(adjusted_risk["funnel_state"], "可準備")
        self.assertEqual(adjusted_risk["strategy_funnel_state"], "可準備")
        self.assertEqual(ordinary_risk["funnel_state"], "不可追高觀察")
        self.assertEqual(ordinary_risk["strategy_funnel_state"], "可準備")
        self.assertIsNotNone(adjusted_risk.get("evidence_adjustment_reason"))
        self.assertIsNone(ordinary_risk.get("evidence_adjustment_reason"))
        self.assertEqual(generator.unheld_prepare_bucket_counts(list(payloads.items()), report_context=context), {
            "可準備": 1,
            "不可追高觀察": 1,
        })

    def test_confirmed_evidence_preserves_overheat_and_rr_hard_blockers(self):
        rr_blocked = self.evidence_payload(confidence=78, decision="WAIT", action=0, rr=0.8, distance=2)
        hot_blocked = self.evidence_payload(confidence=78, decision="WAIT", action=0, rr=1.4, distance=2, heat="HOT")
        with patch.object(generator, "market_theme_summary_evidence", return_value=self.confirmed_market_evidence()):
            context = generator.build_report_context(
                {"RR": rr_blocked, "HOT": hot_blocked},
                {"trade_date": "2026-06-02"},
                datetime(2026, 6, 2),
                strategy_evidence_summary=structured_strategy_evidence("available", row_count=30),
                report_phase="盤中",
            )

        self.assertEqual(generator.unheld_funnel_state("RR", rr_blocked, report_context=context), "等RR修復")
        self.assertEqual(generator.unheld_funnel_state("HOT", hot_blocked, report_context=context), "等冷卻")
        self.assertIsNone(rr_blocked.get("evidence_adjustment_reason"))
        self.assertIsNone(hot_blocked.get("evidence_adjustment_reason"))

    def test_hot_stock_shows_overheat_evidence_unavailable(self):
        hot = self.evidence_payload(confidence=78, decision="WAIT", action=0, rr=1.4, distance=2, heat="HOT")
        hot["market_theme_evidence"] = self.confirmed_market_evidence()
        hot["strategy_sample_evidence"] = {
            "source_status": "available",
            "classification_sample_count": 36,
            "win_rate": 70,
            "avg_return": 2.0,
            "label": "confirmed",
        }
        with patch.object(generator, "market_theme_summary_evidence", return_value=self.confirmed_market_evidence()):
            messages = generator.formatTelegramMessages(
                {"過熱股": hot},
                "",
                None,
                None,
                {"trade_date": "2026-06-02"},
                datetime(2026, 6, 2),
                strategy_evidence_summary={
                    "structured_status": {
                        "status": "available",
                        "source": "daily_signal_snapshot",
                        "classification_sample_count": 36,
                        "missing_fields": [],
                        "completeness": "complete",
                    },
                },
                report_phase="盤中",
            )

        card = card_block(unheld_message(messages), "【過熱股")

        self.assertEqual(hot["result"]["evidence_status"], "unavailable")
        self.assertEqual(hot["result"]["evidence_modifier"], 1.0)
        self.assertEqual(generator.unheld_funnel_state("過熱股", hot, report_context={
            "evidence_manifest": [],
            "evidence": {},
        }), "等冷卻")
        self.assertIn("證據：過熱不適用", card)
        self.assertNotIn("證據 +", card)
        self.assertNotIn("證據：partial", card)

    def test_v20_4_42_postmarket_unheld_gate_attribution_readability_message_list_replay(self):
        rr_wait = self.evidence_payload(confidence=78, decision="BUY", action=0.1, rr=0.98, distance=6)
        rr_wait["stock_code"] = "2330"
        rr_wait_near_breakout = self.evidence_payload(confidence=78, decision="WAIT", action=0, rr=0.99, distance=2)
        rr_wait_near_breakout["stock_code"] = "2324"
        hot_wait = self.evidence_payload(confidence=78, decision="WAIT", action=0, rr=1.4, distance=2, heat="HOT")
        hot_wait["stock_code"] = "2376"
        extreme_wait = self.evidence_payload(confidence=78, decision="WAIT", action=0, rr=0.7, distance=8, heat="EXTREME")
        extreme_wait["stock_code"] = "2344"
        extreme_wait["result"]["entry_quality"] = "D"
        failed = self.evidence_payload(confidence=72, decision="FAIL", action=0, rr=0, distance=9)
        failed["stock_code"] = "2337"
        failed["result"]["structure_phase"] = "FAILED_BREAKOUT"
        failed["result"]["entry_quality"] = "D"
        limit_rebound = self.evidence_payload(confidence=70, decision="WAIT", action=0, rr=1.4, distance=2)
        limit_rebound["stock_code"] = "2303"
        limit_rebound["result"]["price_behavior"] = "LIMIT_REBOUND"
        weak_rebound = self.evidence_payload(confidence=70, decision="WAIT", action=0, rr=1.4, distance=2)
        weak_rebound["stock_code"] = "3481"
        weak_rebound["result"]["price_behavior"] = "WEAK_REBOUND"
        weak_rebound["result"]["structure_phase"] = "WEAK_REBOUND"
        weak_rebound["result"]["entry_quality"] = "D"
        prepare = self.evidence_payload(confidence=86, decision="BUY", action=0.1, rr=1.8, distance=0.5)
        prepare["stock_code"] = "2301"
        prepare["backtest_context"] = {"sample": 36, "reference": "高", "win_rate": 58, "avg_return": 1.2}
        buyable = self.evidence_payload(confidence=86, decision="BUY", action=0.1, rr=1.8, distance=0.5)
        buyable["stock_code"] = "2421"
        buyable["backtest_context"] = {"sample": 36, "reference": "高", "win_rate": 58, "avg_return": 1.2}
        trend = trend_continuation_payload()

        with patch.object(generator, "market_theme_summary_evidence", return_value=self.confirmed_market_evidence()):
            messages = generator.formatTelegramMessages(
                {
                    "台積電": rr_wait,
                    "仁寶": rr_wait_near_breakout,
                    "技嘉": hot_wait,
                    "華邦電": extreme_wait,
                    "旺宏": failed,
                    "聯電": limit_rebound,
                    "群創": weak_rebound,
                    "光寶科": prepare,
                    "智原": trend,
                },
                "FULL DETAIL",
                "建準",
                88,
                {"trade_date": "2026-06-04"},
                datetime(2026, 6, 4),
                strategy_evidence_summary=structured_strategy_evidence("available", row_count=30),
                report_phase="盤後",
            )
        with patch.object(generator, "market_theme_summary_evidence", return_value=self.confirmed_market_evidence()):
            actionable_messages = generator.formatTelegramMessages(
                {
                    "建準": buyable,
                    "智原": trend_continuation_payload(),
                },
                "FULL DETAIL",
                "建準",
                88,
                {"trade_date": "2026-06-04"},
                datetime(2026, 6, 4),
                strategy_evidence_summary=structured_strategy_evidence("available", row_count=30),
                report_phase="盤中",
            )

        summary = summary_message(messages)
        unheld = unheld_message(messages)
        rendered = "\n\n".join(messages)
        actionable_unheld = unheld_message(actionable_messages)
        rr_card = card_block(unheld, "【台積電 2330】")
        rr_near_card = card_block(unheld, "【仁寶 2324】")
        hot_card = card_block(unheld, "【技嘉 2376】")
        extreme_card = card_block(unheld, "【華邦電 2344】")
        failed_card = card_block(unheld, "【旺宏 2337】")
        limit_card = card_block(unheld, "【聯電 2303】")
        weak_card = card_block(unheld, "【群創 3481】")
        prepare_card = card_block(unheld, "【光寶科 2301】")
        buyable_card = card_block(actionable_unheld, "【建準 2421】")
        trend_card = card_block(unheld, "【智原 3231】")
        actionable_trend_card = card_block(actionable_unheld, "【智原 3231】")

        self.assertIn("【06/04 盤後｜v20.4.47】", summary)
        self.assertIn("新倉建議 1", summary)
        self.assertIn("未持倉 9｜趨勢延續 1｜可準備 1（不可買）", summary)
        self.assertIn("僅追蹤 5", summary)
        self.assertIn("淘汰 2", summary)
        self.assertIn("【台積電 2330】👀 等RR修復｜RR不足", rr_card)
        self.assertIn("卡關主因：RR不足", rr_card)
        self.assertIn("量化差距：RR 0.98｜需>=1.5｜差0.52｜距突破 6%｜需<=4%｜差2%", rr_card)
        self.assertIn("原因：RR不足，等待RR修復", rr_card)
        self.assertNotIn("盤後待確認", rr_card)
        self.assertIn("【仁寶 2324】👀 等RR修復｜RR不足", rr_near_card)
        self.assertIn("卡關主因：RR不足", rr_near_card)
        self.assertIn("量化差距：RR 0.99｜需>=1.5｜差0.51", rr_near_card)
        self.assertNotIn("距突破 2%", rr_near_card)
        self.assertNotIn("盤後待確認", rr_near_card)
        self.assertIn("【技嘉 2376】⏳ 等冷卻｜過熱觀察", hot_card)
        self.assertIn("卡關主因：過熱觀察", hot_card)
        self.assertIn("量化差距：熱度 Lv.2｜需降至 Lv.1/觀察以下", hot_card)
        self.assertIn("解鎖：降溫後重新評估", hot_card)
        self.assertNotIn("RR 1.4｜需>=1.5", hot_card)
        self.assertNotIn("進場品質", hot_card)
        self.assertIn("【華邦電 2344】⏳ 等冷卻｜過熱 Lv.3", extreme_card)
        self.assertIn("卡關主因：熱度 Lv.3", extreme_card)
        self.assertIn("量化差距：熱度 Lv.3｜需降至 Lv.1/觀察以下", extreme_card)
        self.assertIn("解鎖：降溫後重新評估", extreme_card)
        self.assertNotIn("RR 0.7｜需>=1.5", extreme_card)
        self.assertNotIn("進場品質 D｜需B以上", extreme_card)
        self.assertIn("【旺宏 2337】⛔ 淘汰｜突破失敗", failed_card)
        self.assertIn("卡關主因：未站回突破區", failed_card)
        self.assertIn("量化差距：距突破區 9%｜需<=4%｜差5%", failed_card)
        self.assertIn("解鎖：重新站回突破區後再評估", failed_card)
        self.assertNotIn("RR 0｜需>=1.5", failed_card)
        self.assertNotIn("RR不可用 / 不作主因", failed_card)
        self.assertIn("【光寶科 2301】🟡 明日準備｜不可買｜開盤後確認", prepare_card)
        self.assertIn("買點：明日準備｜不可下單", prepare_card)
        self.assertIn("卡關主因：開盤確認未完成", prepare_card)
        self.assertIn("量化差距：盤後待開盤確認", prepare_card)
        self.assertIn("解鎖：明日開盤後仍守突破區 / 不追價", prepare_card)
        self.assertIn("依據：RR 達標；量能達標；回測僅輔助", prepare_card)
        self.assertIn("原因：盤後待確認，需開盤後重新確認", prepare_card)
        self.assertNotIn("既有買點與倉位規則通過", prepare_card)
        self.assertNotIn("買點尚未成立/需觸發", prepare_card)
        self.assertNotIn("證據：資料不足", prepare_card)
        self.assertNotIn("卡關主因：", buyable_card)
        self.assertNotIn("量化差距：", buyable_card)
        self.assertNotIn("距突破 0.5%/需<=4%", buyable_card)
        self.assertNotIn("買點距離已觸發/不追價", buyable_card)
        self.assertNotIn("卡關主因：", trend_card)
        self.assertNotIn("量化差距：", trend_card)
        self.assertNotIn("卡關主因：", actionable_trend_card)
        self.assertNotIn("量化差距：", actionable_trend_card)
        self.assertNotIn("買點距離已觸發/不追價", actionable_trend_card)
        self.assertIn("卡關主因：漲跌停鎖定", limit_card)
        self.assertIn("量化差距：需解除鎖定後重新評估", limit_card)
        self.assertIn("卡關主因：反彈力道不足", weak_card)
        self.assertIn("量化差距：需放量轉強後重新評估", weak_card)
        for raw in ["EXTREME", "HOT", "LIMIT_LOCK", "LIMIT_REBOUND", "WEAK_REBOUND", "entry quality", "到達可買差距", "決策證據：來源可追溯", "hard stop", "持倉硬風控"]:
            self.assertNotIn(raw, rendered)
        self.assertNotIn("建議買入", rr_card + hot_card + extreme_card + failed_card)
        self.assertNotIn("可立即買", rr_card + hot_card + extreme_card + failed_card)

    def test_confirmed_evidence_preserves_limit_lock_chase_hard_blocker(self):
        payload = self.evidence_payload(confidence=78, decision="WAIT", action=0, rr=1.4, distance=2)
        payload["market_theme_evidence"] = self.confirmed_market_evidence()
        payload["strategy_sample_evidence"] = self.confirmed_strategy_evidence()
        payload["result"]["price_behavior"] = "LIMIT_LOCK"
        payload["result"]["heat_state"] = "NORMAL"
        payload["result"]["trade_state"] = "AVOID"
        with patch.object(generator, "market_theme_summary_evidence", return_value=self.confirmed_market_evidence()):
            messages = generator.formatTelegramMessages(
                {"追高": payload},
                "",
                None,
                None,
                {"trade_date": "2026-06-02"},
                datetime(2026, 6, 2),
                strategy_evidence_summary=structured_strategy_evidence("available", row_count=30),
                report_phase="盤中",
            )

        artifact_payload = self.evidence_payload(confidence=78, decision="WAIT", action=0, rr=1.4, distance=2)
        artifact_payload["market_theme_evidence"] = self.confirmed_market_evidence()
        artifact_payload["strategy_sample_evidence"] = self.confirmed_strategy_evidence()
        artifact_payload["result"]["price_behavior"] = "LIMIT_LOCK"
        artifact_payload["result"]["heat_state"] = "NORMAL"
        artifact_payload["result"]["trade_state"] = "AVOID"
        with patch.object(generator, "market_theme_summary_evidence", return_value=self.confirmed_market_evidence()):
            context = generator.build_report_context(
                {"追高": artifact_payload},
                {"trade_date": "2026-06-02"},
                datetime(2026, 6, 2),
                strategy_evidence_summary=structured_strategy_evidence("available", row_count=30),
                report_phase="盤中",
            )

        summary = summary_message(messages)
        rendered = "\n\n".join(messages)
        card = card_block(unheld_message(messages), "【追高")
        fields = {field["field_name"]: field for field in context["evidence_manifest"]}
        risk_value = fields["stock.追高.risk"]["value"]

        self.assertEqual(generator.unheld_funnel_state("追高", artifact_payload, report_context=context), "等回測")
        self.assertEqual(risk_value["funnel_state"], "等回測")
        self.assertEqual(risk_value["strategy_funnel_state"], "等回測")
        self.assertIsNone(risk_value.get("evidence_adjustment_reason"))
        self.assertIsNone(artifact_payload.get("evidence_adjustment_reason"))
        self.assertIn("未持倉 1｜僅追蹤 1（等回測）", summary)
        self.assertNotIn("未持倉 1 檔可準備", summary)
        self.assertNotIn("可準備 1（不可買）", summary)
        self.assertIn("【追高 9999】⏳ 等回測｜漲停不追", card)
        self.assertIn("買點：不買，等回測", card)
        self.assertIn("卡關主因：漲跌停鎖定", card)
        self.assertIn("量化差距：需解除鎖定後重新評估", card)
        self.assertNotIn("LIMIT_LOCK", card)
        self.assertNotIn("heat NORMAL/需降溫", card)
        self.assertNotIn("【追高 9999】🟢 可買", card)
        self.assertEqual(payload["result"]["evidence_modifier"], 1.0)
        self.assertIn("RR -（過熱）｜不適用（過熱）｜證據：過熱不適用", card)
        self.assertNotIn("綜合 78｜技術 78", card)
        self.assertNotIn("證據 +", card)
        self.assertNotIn("證據僅調整邊界，不放寬RR/過熱限制", rendered)
        self.assertNotIn("【追高 9999】👀 可準備", rendered)

    def test_v20_4_43_evidence_chain_decision_judgments_cover_eligibility_layers(self):
        buyable = self.evidence_payload(confidence=86, decision="BUY", action=0.1, rr=1.8, distance=0.5)
        buyable["stock_code"] = "2421"
        buyable["strategy_sample_evidence"] = self.confirmed_strategy_evidence()
        prepare = self.evidence_payload(confidence=78, decision="WAIT", action=0, rr=1.6, distance=2)
        prepare["stock_code"] = "2301"
        prepare["market_theme_evidence"] = self.confirmed_market_evidence()
        prepare["strategy_sample_evidence"] = self.confirmed_strategy_evidence()
        trend = trend_continuation_payload()
        failed = self.evidence_payload(confidence=72, decision="FAIL", action=0, rr=0, distance=9)
        failed["stock_code"] = "2337"
        failed["result"]["structure_phase"] = "FAILED_BREAKOUT"
        failed["result"]["entry_quality"] = "D"

        payloads = {
            "建準": buyable,
            "光寶科": prepare,
            "智原": trend,
            "旺宏": failed,
        }
        with patch.object(generator, "market_theme_summary_evidence", return_value=self.confirmed_market_evidence()):
            messages = generator.formatTelegramMessages(
                payloads,
                "FULL DETAIL",
                "建準",
                88,
                {"trade_date": "2026-06-04"},
                datetime(2026, 6, 4),
                strategy_evidence_summary=structured_strategy_evidence("available", row_count=30),
                report_phase="盤中",
            )
            context = generator.build_report_context(
                payloads,
                {"trade_date": "2026-06-04"},
                datetime(2026, 6, 4),
                strategy_evidence_summary=structured_strategy_evidence("available", row_count=30),
                report_phase="盤中",
            )

        rendered = "\n\n".join(messages)
        fields = {field["field_name"]: field for field in context["evidence_manifest"]}
        judgments = context["stock_judgments"]

        self.assertIn("【06/04 盤中｜v20.4.47】", summary_message(messages))
        self.assertEqual(judgments["建準"]["eligibility_state"], "buy")
        self.assertEqual(judgments["建準"]["evidence_status"], "ok")
        self.assertIn("既有買點與倉位規則通過", judgments["建準"]["progress_reasons"])
        self.assertEqual(judgments["光寶科"]["eligibility_state"], "prepare")
        self.assertIn("證據僅調整邊界，不放寬RR/過熱限制", "｜".join(judgments["光寶科"]["progress_reasons"]))
        self.assertEqual(judgments["智原"]["eligibility_state"], "trend_continuation")
        self.assertIn("trend_continuation 同源證據達標", "｜".join(judgments["智原"]["progress_reasons"]))
        self.assertEqual(judgments["旺宏"]["eligibility_state"], "blocked")
        self.assertIn("failed breakout", judgments["旺宏"]["blocking_reasons"])
        for name, judgment in judgments.items():
            self.assertIn("symbol", judgment)
            self.assertIn("primary_action", judgment)
            self.assertIn("evidence_refs", judgment)
            self.assertIn("blocking_reasons", judgment)
            self.assertIn("progress_reasons", judgment)
            self.assertIn(f"stock.{name}.risk", judgment["evidence_refs"])
            self.assertIn(f"stock.{name}.decision_judgment", fields)
            self.assertEqual(fields[f"stock.{name}.decision_judgment"]["value"], judgment)
        self.assertIn("【光寶科 2301】👀 可準備", rendered)
        buy_card = card_block(unheld_message(messages), "【建準 2421】")
        prepare_card = card_block(unheld_message(messages), "【光寶科 2301】")
        trend_card = card_block(unheld_message(messages), "【智原 3231】")
        failed_card = card_block(unheld_message(messages), "【旺宏 2337】")
        self.assertIn("依據：買點成立，倉位規則通過", buy_card)
        self.assertIn("理由：技術條件接近可準備門檻", prepare_card)
        self.assertIn("證據僅調整邊界，不放寬RR/過熱限制", prepare_card)
        self.assertIn("【智原 3231】🟢 趨勢延續買入｜小倉", rendered)
        self.assertIn("依據：趨勢延續同源證據達標，仍限小倉", trend_card)
        self.assertIn("【旺宏 2337】⛔ 淘汰｜突破失敗", rendered)
        self.assertNotIn("決策證據：來源可追溯", rendered)
        self.assertNotIn("hard stop", rendered)

    def test_v20_4_43_evidence_chain_missing_error_conflict_fail_closed(self):
        cases = [
            ("missing", None, "missing", "策略樣本證據不足"),
            ("source-error", structured_strategy_evidence("source-error", row_count=0), "source_error", "策略樣本來源異常"),
            ("conflicting", structured_strategy_evidence("unresolved-conflict", row_count=30), "conflicting", "策略樣本來源衝突"),
        ]
        for label, strategy_summary, expected_status, expected_text in cases:
            with self.subTest(label=label):
                payload = self.evidence_payload(confidence=86, decision="BUY", action=0.1, rr=1.8, distance=0.5)
                payload["stock_code"] = "2454"
                with patch.object(generator, "market_theme_summary_evidence", return_value=self.confirmed_market_evidence()):
                    messages = generator.formatTelegramMessages(
                        {"聯發科": payload},
                        "FULL DETAIL",
                        "聯發科",
                        88,
                        {"trade_date": "2026-06-04"},
                        datetime(2026, 6, 4),
                        strategy_evidence_summary=strategy_summary,
                        report_phase="盤中",
                    )
                    context = generator.build_report_context(
                        {"聯發科": payload},
                        {"trade_date": "2026-06-04"},
                        datetime(2026, 6, 4),
                        strategy_evidence_summary=strategy_summary,
                        report_phase="盤中",
                    )

                rendered = "\n\n".join(messages)
                judgment = context["stock_judgments"]["聯發科"]
                card = card_block(unheld_message(messages), "【聯發科 2454】")

                self.assertEqual(judgment["eligibility_state"], "blocked")
                self.assertEqual(judgment["evidence_status"], expected_status)
                self.assertIn("DB/live restriction: evidence cannot authorize DB write/live Telegram delivery", judgment["blocking_reasons"])
                self.assertIn(expected_text, card)
                self.assertIn("決策依據：", card)
                self.assertNotIn("決策證據：來源可追溯", card)
                self.assertNotIn("【聯發科 2454】🟢 可買", rendered)
                self.assertNotIn("新倉建議", summary_message(messages))

    def test_v20_4_43_holding_hard_stop_judgment_is_visible_and_non_bypass(self):
        payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 94],
            {"shares": 100, "avg_price": 100},
            price=94,
            change=-4.0,
        )
        payload["stock_code"] = "2303"
        payload["position_events"] = {"event_count": 1, "bought_shares": 100}
        payload["holding_decision"] = {
            "action": "停損 100%",
            "level": "STOP_100",
            "shares": 100,
            "note": "硬停損觸發",
            "warning_price": 98,
            "hard_stop_price": 95,
            "allow_add": False,
        }

        messages = generator.formatTelegramMessages(
            {"聯電": payload},
            "FULL DETAIL",
            None,
            None,
            {"trade_date": "2026-06-04"},
            datetime(2026, 6, 4),
            strategy_evidence_summary=structured_strategy_evidence("available", row_count=30),
            report_phase="盤中",
        )
        context = generator.build_report_context(
            {"聯電": payload},
            {"trade_date": "2026-06-04"},
            datetime(2026, 6, 4),
            strategy_evidence_summary=structured_strategy_evidence("available", row_count=30),
            report_phase="盤中",
        )

        card = position_message(messages)
        judgment = context["stock_judgments"]["聯電"]

        self.assertIn("【聯電 2303】📌 停損", card)
        self.assertIn("原因：跌破停損線，避免虧損擴大；風險依據：跌破停損線 1.05%，避免虧損擴大", card)
        self.assertIn("hard stop / holding risk", judgment["blocking_reasons"])
        self.assertIn("DB/live restriction: evidence cannot authorize DB write/live Telegram delivery", judgment["blocking_reasons"])
        self.assertNotIn("live Telegram", card)
        self.assertNotIn("hard stop", card)
        self.assertNotIn("持倉硬風控", card)

    def test_strategy_sample_below_threshold_is_partial_not_decision_eligible(self):
        payload = self.evidence_payload(confidence=80)
        payload["strategy_sample_evidence"] = {
            "source_status": "available",
            "sample": 9,
            "win_rate": 70,
            "avg_return": 2.0,
            "label": "confirmed",
        }
        with patch.object(generator, "market_theme_summary_evidence", return_value=self.missing_market_evidence()):
            context = generator.build_report_context(
                {"低樣本": payload},
                {"trade_date": "2026-06-02"},
                datetime(2026, 6, 2),
                strategy_evidence_summary=structured_strategy_evidence("available", row_count=9),
                report_phase="盤中",
            )

        self.assertEqual(context["evidence"]["strategy_sample"]["status"], "partial")
        self.assertFalse(context["evidence"]["strategy_sample"]["decision_eligible"])
        self.assertEqual(generator.compute_evidence_score(context, "低樣本")[1], "partial")
        self.assertIsNone(payload.get("evidence_adjustment_reason"))

    def test_pick_best_stock_and_watchlist_sort_use_final_confidence(self):
        higher_technical = self.evidence_payload(confidence=90, decision="BUY", action=0.2)
        lower_technical = self.evidence_payload(confidence=80, decision="BUY", action=0.2)
        higher_technical["result"]["final_confidence"] = 81
        lower_technical["result"]["final_confidence"] = 92

        best, _score = generator.pick_best_stock({
            "技術高": higher_technical["result"],
            "綜合高": lower_technical["result"],
        })
        ordered = generator.sort_watchlist_grouped([
            ("技術高", higher_technical),
            ("綜合高", lower_technical),
        ])

        self.assertEqual(best, "綜合高")
        self.assertEqual(ordered[0][1][0], "綜合高")

    def test_market_theme_single_day_does_not_become_decision_eligible_or_relax_chase(self):
        payload = self.evidence_payload(confidence=78, decision="WAIT", action=0, distance=9)
        with patch.object(generator, "market_theme_summary_evidence", return_value=self.confirmed_market_evidence("single_day")):
            context = generator.build_report_context(
                {"單日": payload},
                {"trade_date": "2026-06-02"},
                datetime(2026, 6, 2),
                strategy_evidence_summary=structured_strategy_evidence("available", row_count=30),
                report_phase="盤中",
            )

        self.assertFalse(context["evidence"]["market_theme"]["decision_eligible"])
        self.assertNotEqual(generator.compute_evidence_score(context, "單日")[1], "confirmed")
        self.assertEqual(generator.unheld_funnel_state("單日", payload, report_context=context), "等回測")

    def test_market_theme_supporting_trend_is_not_strong_boundary_evidence(self):
        payload = self.evidence_payload(confidence=78, decision="WAIT", action=0, rr=1.4, distance=2)
        payload["market_theme_evidence"] = self.confirmed_market_evidence("supporting_trend")
        payload["strategy_sample_evidence"] = {
            "source_status": "available",
            "sample": 30,
            "win_rate": 48,
            "avg_return": 0.2,
            "label": "supporting",
        }
        payload["result"]["market_grade"] = "C"
        payload["result"]["entry_quality"] = "C"
        with patch.object(generator, "market_theme_summary_evidence", return_value=self.confirmed_market_evidence("supporting_trend")):
            messages = generator.formatTelegramMessages(
                {"支持趨勢": payload},
                "",
                None,
                None,
                {"trade_date": "2026-06-02"},
                datetime(2026, 6, 2),
                strategy_evidence_summary=structured_strategy_evidence("available", row_count=30),
                report_phase="盤中",
            )

        artifact_payload = self.evidence_payload(confidence=78, decision="WAIT", action=0, rr=1.4, distance=2)
        artifact_payload["market_theme_evidence"] = self.confirmed_market_evidence("supporting_trend")
        artifact_payload["strategy_sample_evidence"] = {
            "source_status": "available",
            "sample": 30,
            "win_rate": 48,
            "avg_return": 0.2,
            "label": "supporting",
        }
        artifact_payload["result"]["market_grade"] = "C"
        artifact_payload["result"]["entry_quality"] = "C"
        with patch.object(generator, "market_theme_summary_evidence", return_value=self.confirmed_market_evidence("supporting_trend")):
            context = generator.build_report_context(
                {"支持趨勢": artifact_payload},
                {"trade_date": "2026-06-02"},
                datetime(2026, 6, 2),
                strategy_evidence_summary=structured_strategy_evidence("available", row_count=30),
                report_phase="盤中",
            )

        score, status = generator.compute_evidence_score(context, "支持趨勢")
        fields = {field["field_name"]: field for field in context["evidence_manifest"]}
        risk_value = fields["stock.支持趨勢.risk"]["value"]
        rendered = "\n\n".join(messages)

        self.assertEqual(context["evidence"]["market_theme"]["status"], "supporting")
        self.assertFalse(context["evidence"]["market_theme"]["decision_eligible"])
        self.assertFalse(fields["evidence.market_theme"]["decision_eligible"])
        self.assertEqual(status, "supporting")
        self.assertIsNotNone(score)
        self.assertLess(context["evidence"]["market_theme"]["score"], 1.0)
        self.assertLess(artifact_payload["result"]["evidence_modifier"], 1.15)
        self.assertNotEqual(generator.unheld_funnel_state("支持趨勢", artifact_payload, report_context=context), "可準備")
        self.assertNotEqual(risk_value["funnel_state"], "可準備")
        self.assertNotEqual(risk_value["strategy_funnel_state"], "可準備")
        self.assertIsNone(risk_value.get("evidence_adjustment_reason"))
        self.assertIsNone(artifact_payload.get("evidence_adjustment_reason"))
        self.assertNotIn("證據僅調整邊界，不放寬RR/過熱限制", rendered)
        self.assertNotIn("產業主題 confirmed", rendered)
        self.assertNotIn("【支持趨勢 9999】👀 可準備", rendered)

    def test_b5_tracking_split_matches_card_states_and_tracking_total(self):
        next_day = self.evidence_payload(confidence=64, decision="WAIT", action=0, rr=1.4, distance=2)
        next_day["result"]["price_behavior"] = "LIMIT_REBOUND"
        pullback = self.evidence_payload(confidence=64, decision="WAIT", action=0, rr=1.4, distance=9)
        cooldown = self.evidence_payload(confidence=64, decision="WAIT", action=0, rr=1.4, distance=2, heat="HOT")
        cooldown["result"]["trade_state"] = "EXTENDED"
        payloads = {
            "漲停反彈": next_day,
            "等回測股": pullback,
            "等冷卻股": cooldown,
        }
        watch_items = list(payloads.items())

        with patch.object(generator, "market_theme_summary_evidence", return_value=self.missing_market_evidence()):
            messages = generator.formatTelegramMessages(
                payloads,
                "",
                None,
                None,
                {"trade_date": "2026-06-02"},
                datetime(2026, 6, 2),
                strategy_evidence_summary=structured_strategy_evidence("available", row_count=30),
                report_phase="盤中",
            )
            context = generator.build_report_context(
                payloads,
                {"trade_date": "2026-06-02"},
                datetime(2026, 6, 2),
                strategy_evidence_summary=structured_strategy_evidence("available", row_count=30),
                report_phase="盤中",
            )

        funnel = generator.build_unheld_funnel(watch_items, report_context=context)
        funnel_text = generator.format_unheld_funnel(watch_items, report_context=context)
        unheld = unheld_message(messages)

        self.assertEqual(generator.tomorrow_watch_state("漲停反彈", next_day), "隔日確認")
        self.assertEqual(generator.unheld_funnel_state("漲停反彈", next_day, report_context=context), "隔日確認")
        self.assertEqual(generator.unheld_tracking_only_count(funnel), 3)
        self.assertEqual(sum(len(funnel[label]) for label in ["隔日確認", "等冷卻", "等回測", "等RR修復", "等量能"]), 3)
        self.assertIn("僅追蹤 3", funnel_text)
        self.assertIn("未持倉 3｜可買 0｜不可追高觀察 0（不可買）｜隔日確認 1｜僅追蹤 3（等冷卻1/等回測1）｜淘汰 0", funnel_text)
        self.assertIn("隔日確認 1｜僅追蹤 3", funnel_text)
        self.assertIn("【漲停反彈 9999】👀 隔日確認", unheld)
        self.assertIn("【等回測股 9999】👀 不可追高觀察", unheld)
        self.assertIn("【等冷卻股 9999】⏳ 等冷卻", unheld)


if __name__ == "__main__":
    unittest.main()
