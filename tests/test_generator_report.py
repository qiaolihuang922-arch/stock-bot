import unittest
import ast
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from datetime import datetime

from core import generator
from presentation import report as presentation_report
from core.signal_snapshot import analyze_ohlcv_snapshot


VOL_ATTACK = [1000] * 19 + [1800]


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


def summary_message(messages):
    return next(
        message for message in messages
        if f"｜{generator.VERSION}】" in message and "簡報＋資料依據" in message
    )


def position_message(messages):
    return next(message for message in messages if "【持倉標的】" in message)


def unheld_message(messages):
    return next(message for message in messages if "【未持倉標的】" in message)


def detail_message(messages):
    return next(message for message in messages if message.startswith("【Details Backup】"))


def evidence_message(messages):
    return next(message for message in messages if "簡報＋資料依據" in message)


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
        self.assertIn("｜v20.4.21】", summary)
        self.assertIn("🧾 v20.4.21 簡報＋資料依據", summary)
        self.assertIn("新倉：無有效進場", summary)
        self.assertIn("資料依據", summary)
        self.assertIn("市場 / 題材背景：短期背景資料不足以形成可靠背景", summary)
        self.assertIn("策略樣本：本輪缺少可驗證樣本，可靠度低，未納入買賣判斷。", summary)
        self.assertIn("持倉 / 價格 / 候選資料：部分持倉或候選資料不足", summary)
        for term in FORBIDDEN_SHORT_EVIDENCE_TERMS:
            self.assertNotIn(term, summary)
        self.assertNotIn("今日可買", summary)
        self.assertNotIn("confirmed", summary)
        self.assertIn("未持倉資料只支持分類觀察，不支持直接進場", detail)

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
        self.assertIn("持倉 / 價格 / 候選資料：部分持倉或候選資料不足", summary)
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

    def test_v20_2_1_holding_card_always_shows_breakout_distance_when_available(self):
        cases = [
            (-1, "已突破（-1%）"),
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
            (-1, "已突破（-1%）"),
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
        self.assertIn("策略樣本：不可用，本次不納入判斷", unheld_message(messages))
        self.assertIn("📊 市場：", summary_message(messages))
        self.assertIn("📌 持倉：智原", summary_message(messages))
        self.assertIn("🧭 今日結論：", summary_message(messages))
        self.assertIn("✅ 今日盤中交易執行", summary_message(messages))
        self.assertIn("1. 智原｜+0.85%｜加碼10｜加碼後守警戒價", summary_message(messages))
        self.assertIn("未持倉 1 檔只等觸發，不列入今日盤中交易執行", summary_message(messages))
        self.assertNotIn("建準｜等RR修復｜不追價，等RR達標", summary_message(messages))
        self.assertIn("未持倉漏斗（非執行）：", summary_message(messages))
        self.assertIn("未持倉總數 1 檔", summary_message(messages))
        self.assertIn("可買 0｜可準備 0（不可買）｜僅追蹤 1｜淘汰 0", summary_message(messages))
        self.assertIn("其中僅追蹤 1 檔拆分：等RR修復 1", summary_message(messages))
        self.assertIn("可準備 0（不可買）", summary_message(messages))
        self.assertIn("等RR修復 1", summary_message(messages))
        self.assertIn("📎 詳情索引：持倉 1｜交易執行 1｜僅追蹤 1｜淘汰 0", summary_message(messages))
        self.assertNotIn("完整詳情備份", "\n".join(messages))

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
        self.assertIn("決策：續抱觀察，暫不加碼", position_msg)

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
            report_phase="盤中",
        )

        self.assertIn("交易執行 2 項；持倉風控檢查 1 檔；未持倉無追蹤", summary_message(messages))
        self.assertIn("1. 智原｜+0.85%｜加碼10｜加碼後守警戒價", summary_message(messages))
        self.assertIn("2. 建準｜可買｜分批，不追價", summary_message(messages))
        self.assertIn("未持倉總數 1 檔", summary_message(messages))
        self.assertIn("可買 1｜可準備 0（不可買）｜僅追蹤 0｜淘汰 0", summary_message(messages))
        self.assertNotIn("其中僅追蹤 0 檔拆分", summary_message(messages))
        self.assertIn("📎 詳情索引：持倉 1｜交易執行 2｜淘汰 0", summary_message(messages))
        self.assertNotIn("未持倉 0 檔僅追蹤", summary_message(messages))
        self.assertNotIn("其餘 0 檔僅追蹤", summary_message(messages))

    def test_unheld_funnel_prepare_count_has_separate_tracking_parent(self):
        states = {
            "準備股": "可準備",
            "冷卻一": "等冷卻",
            "冷卻二": "等冷卻",
            "RR股": "等RR修復",
        }

        with patch.object(generator, "unheld_funnel_state", side_effect=lambda name, _data, **_kwargs: states[name]):
            text = generator.format_unheld_funnel([(name, {}) for name in states])

        self.assertIn("未持倉總數 4 檔", text)
        self.assertIn("可買 0｜可準備 1（不可買）｜僅追蹤 3｜淘汰 0", text)
        self.assertIn("其中僅追蹤 3 檔拆分：等冷卻 2、等RR修復 1", text)
        self.assertIn("非執行準備/追蹤合計 4 檔（可準備 1｜僅追蹤 3）", text)
        self.assertNotIn("非執行追蹤 4 檔，僅追蹤不可買", text)
        self.assertNotIn("其中：等冷卻 2、等回測 0、等RR修復 1、等量能 0", text)

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
            strategy_evidence_summary=(
                "📊 策略證據 v20.0\n"
                "策略樣本 / 分類回測\n"
                "狀態：不可用\n"
                "原因：classification backtest 樣本不足（有效樣本 3）\n"
                "解讀：本次不把策略樣本納入判斷；個股決策只看既有買點與風控。\n"
                "狀態碼：insufficient-sample"
            ),
        )

        summary = summary_message(messages)
        evidence = evidence_message(messages)
        self.assertNotIn("📊 策略證據 v20.0", summary)
        self.assertNotIn("策略樣本 / 分類回測", summary)
        self.assertIn("v20.4.21 簡報＋資料依據", evidence)
        self.assertIn("策略樣本：本次不可用（原因：樣本不足），單檔卡片不重複列示。", evidence)
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
        self.assertIn("未持倉總數 4 檔", summary_msg)
        self.assertIn("可買 0｜可準備 2（不可買）｜僅追蹤 1｜淘汰 1", summary_msg)
        self.assertIn("其中僅追蹤 1 檔拆分：等RR修復 1", summary_msg)
        self.assertIn("非執行準備/追蹤合計 3 檔（可準備 2｜僅追蹤 1）", summary_msg)
        self.assertIn("未持倉 2 檔可準備、1 檔僅追蹤，等觸發，不列入今日盤中交易執行", summary_msg)
        self.assertIn("強勢準備：\n- 漲停鎖價：聯電 不可追高，待開板回測\n- 過熱降溫：光寶科 不可買，待降溫後重評", summary_msg)
        self.assertIn("淘汰 1 檔｜主因：市場弱｜詳情見未持倉卡", summary_msg)
        self.assertLess(unheld_msg.index("【聯電 2303】"), unheld_msg.index("【光寶科 2301】"))
        self.assertLess(unheld_msg.index("【光寶科 2301】"), unheld_msg.index("【建準 2421】"))
        self.assertLess(unheld_msg.index("【建準 2421】"), unheld_msg.index("【旺宏 2337】"))
        self.assertIn("【聯電 2303】👀 可準備｜漲停鎖價", unheld_msg)
        self.assertIn("【光寶科 2301】👀 可準備｜過熱降溫", unheld_msg)
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
        self.assertIn("可買 0｜可準備 0（不可買）｜僅追蹤 1｜淘汰 0", summary_message(messages))
        self.assertIn("其中僅追蹤 1 檔拆分：等回測 1", summary_message(messages))
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

        self.assertIn("v20.4.21", summary_message(messages))
        self.assertIn("📡 資料：即時價 realtime｜日線 yahoo", summary_message(messages))
        self.assertIn("🧭 今日結論：R3 進攻偏熱；交易執行：無新增下單；持倉風控檢查 5 檔；未持倉 4 檔可準備、2 檔僅追蹤", summary_message(messages))
        self.assertIn("🧭 原因：強勢股多過熱，RR不足，不追高", summary_message(messages))
        self.assertIn("✅ 今日盤中交易執行", summary_message(messages))
        self.assertIn("無新增下單", summary_message(messages))
        self.assertIn("持倉風控檢查", summary_message(messages))
        self.assertIn("1. 英業達｜+19.37%｜核心風控觀察｜守警戒價", summary_message(messages))
        self.assertIn("2. 智原｜-0.59%｜洗盤警戒｜跌破警戒升級風控", summary_message(messages))
        self.assertIn("未持倉 4 檔可準備、2 檔僅追蹤，等觸發，不列入今日盤中交易執行", summary_message(messages))
        self.assertIn("未持倉漏斗（非執行）：", summary_message(messages))
        self.assertIn("未持倉總數 7 檔", summary_message(messages))
        self.assertIn("可買 0｜可準備 4（不可買）｜僅追蹤 2｜淘汰 1", summary_message(messages))
        self.assertIn("其中僅追蹤 2 檔拆分：等RR修復 2", summary_message(messages))
        self.assertIn("非執行準備/追蹤合計 6 檔（可準備 4｜僅追蹤 2）", summary_message(messages))
        self.assertIn("📎 詳情索引：持倉 5｜交易執行 0｜可準備 4｜僅追蹤 2｜淘汰 1", summary_message(messages))
        self.assertIn("淘汰 1 檔｜主因：弱反彈待確認｜詳情見未持倉卡", summary_message(messages))
        self.assertIn("【光寶科 2301】👀 可準備｜過熱降溫", unheld_message(messages))
        self.assertIn("【建準 2421】👀 等RR修復｜RR不足", unheld_message(messages))
        self.assertIn("【旺宏 2337】⛔ 淘汰｜弱反彈待確認", unheld_message(messages))
        self.assertIn("新倉 RR：不適用（既有持倉）", position_message(messages))
        self.assertIn("RR -（過熱）", unheld_message(messages))
        self.assertIn("RR -（弱勢）", unheld_message(messages))

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
            report_phase="盤中",
        )

        self.assertIn("1. 建準｜可買｜分批，不追價", summary_message(messages))
        self.assertIn("未持倉總數 1 檔", summary_message(messages))
        self.assertIn("可買 1｜可準備 0（不可買）｜僅追蹤 0｜淘汰 0", summary_message(messages))
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
            report_phase="盤中",
        )

        self.assertIn("1. 建準｜可買｜分批，不追價", summary_message(messages))
        self.assertIn("未持倉總數 2 檔", summary_message(messages))
        self.assertIn("可買 1｜可準備 0（不可買）｜僅追蹤 0｜淘汰 1", summary_message(messages))
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

        self.assertIn("未持倉總數 1 檔", summary_message(messages))
        self.assertIn("可買 0｜可準備 0（不可買）｜僅追蹤 1｜淘汰 0", summary_message(messages))
        self.assertIn("其中僅追蹤 1 檔拆分：等量能 1", summary_message(messages))
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
        self.assertIn("未持倉總數 2 檔", summary_message(messages))
        self.assertIn("可買 0｜可準備 0（不可買）｜僅追蹤 2｜淘汰 0", summary_message(messages))
        self.assertIn("其中僅追蹤 2 檔拆分：等RR修復 2", summary_message(messages))
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
        self.assertIn("【05/29 盤中｜v20.4.21】", summary)
        self.assertIn("追蹤最強：\n- 旺宏 修復中｜連續觀察 4 天，不可買，待觸發", summary)
        self.assertIn("可買 0｜可準備 1（不可買）｜僅追蹤 0｜淘汰 0", summary)
        self.assertIn("【旺宏 2337】👀 可準備", unheld)
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
        self.assertIn("【05/28 盤後｜v20.4.21】", summary)
        self.assertIn("📌 盤後簡報", summary)
        self.assertIn("結論：今日無有效新倉；既有持倉以收盤後風控觀察為主。", summary)
        self.assertIn("明日前確認：觀察持倉是否跌破警戒。", summary)
        self.assertNotIn("技嘉｜明日風控｜加碼10", summary)
        self.assertNotIn("加碼後守警戒價，量價未延續則停止加碼", summary)

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
        self.assertIn("【05/28 盤後｜v20.4.21】", summary)
        self.assertIn("📌 盤後簡報", summary)
        self.assertIn("結論：今日無有效新倉；既有持倉以收盤後風控觀察為主。", summary)
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
        )

        self.assertIn("v20.4.21", summary_message(messages))
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

        self.assertIn("【05/29 盤中｜v20.4.21】", summary)
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
        self.assertIn("【05/29 盤中｜v20.4.21】", summary)
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
        self.assertIn("【05/31 假日｜v20.4.21】", summary)
        self.assertIn("【英業達 2356】📌 第二段停利後觀察", card)
        self.assertIn("今日 最近交易日賣 187股", card)
        self.assertIn(context, card)
        self.assertNotIn(f"英業達｜已執行｜{context}", summary)
        self.assertIn("持倉：依第一則既有卡片處理，不新增第二個主行動。", summary)
        self.assertIn("持倉與價格資料可支持風控檢查", summary)
        self.assertIn("未持倉資料只支持分類觀察，不支持直接進場", summary)
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
            )

        summary = summary_message(messages)
        position = position_message(messages)
        unheld = unheld_message(messages)

        self.assertIn("【05/28 盤中｜v20.4.21】", summary)
        self.assertIn("✅ 今日盤中交易執行", summary)
        self.assertNotIn("明日執行", summary)
        self.assertIn("交易執行 1 項；持倉風控檢查 1 檔；已執行 1 項不重複", summary)
        self.assertIn("光寶科｜可買｜首筆最多 30%，總上限 60%｜分批，不追價", summary)
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

        self.assertIn("【05/28 盤中｜v20.4.21】", summary)
        self.assertIn("🧭 今日結論：", summary)
        self.assertIn("交易執行：無新增下單", summary)
        self.assertIn("✅ 今日盤中交易執行\n無新增下單", summary)
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
        self.assertIn("未持倉總數 3 檔", summary)
        self.assertIn("可買 0｜可準備 0（不可買）｜僅追蹤 1｜淘汰 2", summary)
        self.assertIn("其中僅追蹤 1 檔拆分：等RR修復 1", summary)
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

        self.assertIn("【05/28 盤中｜v20.4.21】", summary)
        self.assertIn("市場 / 題材背景：短期背景資料不足以形成可靠背景，只作觀察，不作買點。", summary)
        self.assertNotIn("證據：production 來源不足，不作確認。", summary)
        self.assertNotIn("詳情：runtime 觀察僅供診斷，非確認來源。", summary)
        self.assertIn("🧭 主線：市場偏多但買點未成立。", summary)
        self.assertIn("🧭 執行：新增買點未成立，先等回測，不追高。", summary)
        self.assertIn("🧭 新倉：無有效進場。", summary)
        self.assertLess(
            summary.index("🧭 新倉：無有效進場。"),
            summary.index("市場 / 題材背景：短期背景資料不足以形成可靠背景"),
        )
        self.assertNotIn("🧭 主線：AI / 電子供應鏈仍偏多。", summary)
        self.assertIn("交易執行：無新增下單", summary)
        self.assertIn("未持倉 1 檔可準備、1 檔僅追蹤，等觸發，不列入今日盤中交易執行", summary)
        self.assertIn("強勢準備：\n- 過熱降溫：台達電 不可買，待降溫後重評", summary)
        self.assertIn("可買 0｜可準備 1（不可買）｜僅追蹤 1｜淘汰 1", summary)
        self.assertIn("其中僅追蹤 1 檔拆分：等回測 1", summary)
        self.assertIn("淘汰 1 檔｜主因：突破失敗｜詳情見未持倉卡", summary)
        self.assertIn("【台積電 2330】📌 核心續抱", position)
        self.assertIn("決策：核心續抱，暫不加碼", position)
        self.assertIn("下一步：保留核心倉，觀察是否轉弱", position)
        self.assertIn("台積電｜+26.00%｜核心續抱｜守警戒價，觀察是否轉弱", summary)
        self.assertEqual(generator.position_summary_note("台積電", holding_payload), "現有持倉保留，按風控續抱；新增倉位等觸發")
        self.assertNotIn("主線持倉保留", summary + position)
        self.assertIn("【世芯-KY 3661】⏳ 等回測｜遠離觸發", unheld)
        self.assertIn("買點：不買，等回測", unheld)
        self.assertIn("【台達電 2308】👀 可準備｜過熱降溫", unheld)
        self.assertIn("買點：不可買，待降溫後重評", unheld)
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

        self.assertIn("📊 市場：進攻偏熱｜R3", summary)
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

        self.assertIn("【05/29 盤中｜v20.4.21】", summary)
        self.assertIn("🧭 今日結論：R3 進攻偏熱；交易執行：無新增下單；未持倉 3 檔可準備、1 檔僅追蹤", summary)
        self.assertIn("市場 / 題材背景：短期背景資料不足以形成可靠背景，只作觀察，不作買點。", summary)
        self.assertNotIn("證據：production 來源不足，不作確認。", summary)
        self.assertNotIn("詳情：runtime 觀察僅供診斷，非確認來源。", summary)
        self.assertIn("強勢準備：\n- 漲停鎖價：A 不可追高，待開板回測\n- 過熱降溫：B 不可買，待降溫後重評\n- 突破回測：C 待觸發，不追高", summary)
        self.assertIn("可買 0｜可準備 3（不可買）｜僅追蹤 1｜淘汰 1", summary)
        self.assertIn("其中僅追蹤 1 檔拆分：等RR修復 1", summary)
        self.assertIn("【A 0001】👀 可準備｜漲停鎖價", unheld)
        self.assertIn("買點：不可追高，待開板回測", unheld)
        self.assertIn("【B 0002】👀 可準備｜過熱降溫", unheld)
        self.assertIn("買點：不可買，待降溫後重評", unheld)
        self.assertIn("【C 0003】👀 可準備｜突破回測", unheld)
        self.assertIn("買點：待觸發，不追高", unheld)
        self.assertNotIn("市場 / 題材證據：absent", summary)
        self.assertNotIn("市場沒有證據", summary)
        self.assertNotIn("題材不存在", summary)
        self.assertNotIn("A｜可買", summary + unheld)
        self.assertNotIn("B｜可買", summary + unheld)
        self.assertNotIn("C｜可買", summary + unheld)

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

        self.assertIn("【05/29 盤中｜v20.4.21】", summary)
        self.assertIn("🧭 今日結論：R3 進攻偏熱；交易執行：無新增下單；未持倉 6 檔可準備、1 檔僅追蹤", summary)
        self.assertIn(
            "強勢準備：\n"
            "- 漲停鎖價：A 不可追高，待開板回測\n"
            "- 過熱降溫：B 不可買，待降溫後重評\n"
            "- 過熱降溫：D 不可買，待降溫後重評\n"
            "- 另 3 檔：過熱降溫 1、突破回測 2，見詳情",
            summary,
        )
        strong_prepare_section = summary.split("強勢準備：", 1)[1].split("\n\n", 1)[0]
        self.assertEqual(strong_prepare_section.count("\n- "), 4)
        self.assertNotIn("同狀態", strong_prepare_section)
        self.assertNotIn("C 待觸發", strong_prepare_section)
        self.assertNotIn("E 待觸發", strong_prepare_section)
        self.assertNotIn("F 待觸發", strong_prepare_section)
        self.assertIn("可買 0｜可準備 6（不可買）｜僅追蹤 1｜淘汰 1", summary)
        self.assertIn("其中僅追蹤 1 檔拆分：等RR修復 1", summary)
        for name, code, label in [
            ("A", "0001", "漲停鎖價"),
            ("B", "0002", "過熱降溫"),
            ("C", "0003", "突破回測"),
            ("D", "0004", "過熱降溫"),
            ("E", "0005", "過熱降溫"),
            ("F", "0006", "突破回測"),
        ]:
            self.assertIn(f"【{name} {code}】👀 可準備｜{label}", unheld)
        self.assertIn("【G 0007】👀 等RR修復｜RR不足", unheld)
        self.assertIn("【H 0008】⛔ 淘汰｜突破失敗", unheld)
        self.assertNotIn("A｜可買", summary + unheld)
        self.assertNotIn("B｜可買", summary + unheld)
        self.assertNotIn("C｜可買", summary + unheld)
        self.assertNotIn("D｜可買", summary + unheld)
        self.assertNotIn("E｜可買", summary + unheld)
        self.assertNotIn("F｜可買", summary + unheld)

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

        self.assertIn("【05/29 盤後｜v20.4.21】", summary)
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

        self.assertIn("【05/28 盤中｜v20.4.21】", summary)
        self.assertIn("🧭 主線：市場偏多但買點未成立。", summary)
        self.assertIn("🧭 新倉：無有效進場。", summary)
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

        with patch.object(generator, "get_market_phase", side_effect=["盤中", "盤後"]) as phase_mock:
            messages = generator.formatTelegramMessages(
                {"光寶科": payload},
                "FULL DETAIL",
                "光寶科",
                88,
                "🟡 局部機會",
                datetime(2026, 5, 28),
            )

        summary = summary_message(messages)
        unheld = unheld_message(messages)

        self.assertEqual(phase_mock.call_count, 1)
        self.assertIn("【05/28 盤中｜v20.4.21】", summary)
        self.assertIn("✅ 今日盤中交易執行", summary)
        self.assertIn("光寶科｜可買｜分批，不追價", summary)
        self.assertIn("【光寶科 2301】🟢 可買｜10%倉｜買點成立", unheld)
        self.assertIn("盤中觸發：", unheld)
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

        with patch.object(generator, "get_market_phase", return_value="盤後"):
            messages = generator.formatTelegramMessages(
                {"光寶科": payload},
                "FULL DETAIL",
                "光寶科",
                88,
                "🟡 局部機會",
                datetime(2026, 5, 28),
            )

        summary = summary_message(messages)
        unheld = unheld_message(messages)

        self.assertIn("【05/28 盤後｜v20.4.21】", summary)
        self.assertIn("📌 盤後簡報", summary)
        self.assertIn("結論：新倉候選 1 檔需明日開盤前確認", summary)
        self.assertIn("明日前確認：新倉候選需開盤後重新確認有效進場。", summary)
        self.assertIn("【光寶科 2301】🟢 明日追蹤｜10%倉｜買點成立", unheld)
        self.assertIn("買點：盤後追蹤｜開盤後確認｜不追價", unheld)
        self.assertIn("明日觸發：", unheld)
        self.assertNotIn("✅ 今日盤中交易執行", summary)
        self.assertNotIn("交易執行 1", summary)
        self.assertNotIn("存在合格買點，分批執行", summary)
        self.assertNotIn("【光寶科 2301】🟢 可買｜10%倉", unheld)
        self.assertNotIn("買點：可買｜建議 10%倉", unheld)

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
        self.assertIn("｜v20.4.21】", summary_message(messages))
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
        self.assertIn("【06/01 盤中｜v20.4.21】", messages[0])
        self.assertIn("【06/01 盤中｜v20.4.21】", messages[1])
        self.assertIn("【06/01 盤中｜v20.4.21】", messages[2])
        self.assertNotIn("v20.4.11", "\n\n".join(messages))
        self.assertIn("智原", messages[0])
        self.assertIn("續抱", messages[0])
        self.assertIn("建準", messages[1])
        self.assertNotIn("智原", messages[1])
        self.assertNotIn("建準", messages[0])
        self.assertIn("🧾 v20.4.21 簡報＋資料依據", messages[2])
        self.assertEqual(messages[2].count("\n決策簡報\n"), 1)
        self.assertEqual(messages[2].count("\n資料依據\n"), 1)
        self.assertIn("持倉：依第一則既有卡片處理，不新增第二個主行動。", messages[2])
        self.assertIn("新倉：無有效進場。", messages[2])
        self.assertIn("策略樣本：本輪缺少可驗證樣本，可靠度低，未納入買賣判斷。", messages[2])
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
        self.assertIn("持倉與價格資料可支持風控檢查", evidence_message(messages))
        self.assertIn("未持倉資料只支持分類觀察，不支持直接進場", evidence_message(messages))
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
        self.assertIn("策略樣本本輪不採用", evidence_message(messages))
        self.assertIn("策略樣本：本輪缺少可驗證樣本，可靠度低，未納入買賣判斷。", evidence_message(messages))
        self.assertIn("候選資料不足", evidence_message(messages))
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
            strategy_evidence_summary="📊 策略證據 v20.0\n狀態：不可用\n原因：樣本不足（有效樣本 0）",
            report_phase="盤中",
        )

        evidence = evidence_message(messages)
        rendered = "\n\n".join(messages)
        self.assertEqual(len(messages), 3)
        self.assertIs(messages[0], position_message(messages))
        self.assertIs(messages[1], unheld_message(messages))
        self.assertIs(messages[2], evidence)
        self.assertIn("新倉：無有效進場。", evidence)
        self.assertIn("策略樣本本輪不採用", evidence)
        self.assertIn("策略樣本：本輪缺少可驗證樣本，可靠度低，未納入買賣判斷。", evidence)
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
        self.assertIn("新倉 RR：不適用（既有持倉）", position)
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
            "action": "新倉風控觀察",
            "level": "NEW_POSITION_RISK_WATCH",
            "warning_price": 113,
            "hard_stop_price": 109,
            "allow_add": False,
        }
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
            strategy_evidence_summary="📊 策略證據 v20.0\n狀態：不可用\n原因：樣本不足（有效樣本 3）",
            report_phase="盤後",
        )

        position = position_message(messages)
        unheld = unheld_message(messages)
        brief = evidence_message(messages)
        rendered = "\n\n".join(messages)

        self.assertIn("📌 盤後簡報", brief)
        self.assertNotIn("今日交易\n新增交易建議：無", brief)
        self.assertNotIn("持倉風控檢查\n1.", brief)
        self.assertEqual(rendered.count("策略樣本：本次不可用（原因：樣本不足），單檔卡片不重複列示。"), 1)
        self.assertNotIn("策略樣本：不可用，本次不納入判斷", position)
        self.assertNotIn("策略樣本：不可用，本次不納入判斷", unheld)
        self.assertNotIn("missing-source", brief)
        self.assertNotIn("盤中留意", rendered)
        self.assertNotIn("盤中觸發", rendered)
        self.assertNotIn("即時進場", rendered)
        self.assertNotIn("盤中先觀察", rendered)
        self.assertNotIn("盤中觀察修復狀況", rendered)
        self.assertIn("下一步：明日觀察是否守住警戒，未修復再降級", position)
        self.assertIn("新倉 RR：不適用（既有持倉）", position)
        self.assertNotRegex(position, r"數據：RR 2\.73")
        self.assertIn("數據：RR 2.4", unheld)
        self.assertNotIn("資料：現價與 OHLCV 已確認；RR/分數/量能為模型推算", unheld)
        self.assertIn("未持倉資料只支持分類觀察，不支持直接進場。", brief)
        self.assertIn("持倉與價格資料可支持風控檢查", brief)
        self.assertNotIn("交易證據日", rendered)
        self.assertNotIn("策略勝率", rendered)
        self.assertNotIn("勝率證據", rendered)

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
            strategy_evidence_summary="📊 策略證據 v20.0\n狀態：不可用\n原因：樣本不足（有效樣本 3）",
            report_phase="盤中",
        )

        unheld = unheld_message(messages)
        evidence = evidence_message(messages)
        self.assertIn("策略樣本：不可用，本次不納入判斷", unheld)
        self.assertNotIn("樣本35", unheld)
        self.assertNotIn("3日勝率71%", unheld)
        self.assertNotIn("相對+2.4%", unheld)
        self.assertIn("策略樣本：樣本不足，本次不納入買賣判斷。", evidence)

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

        self.assertEqual(context["report_context"]["version"], "v20.4.21")
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

        self.assertIn("🧾 v20.4.21 簡報＋資料依據", summary_message(messages))
        self.assertNotIn("Source：核心價格 available；持倉 available；策略樣本 missing-source；market/theme available", summary_message(messages))
        self.assertNotIn("📊 策略證據 v20.0", summary_message(messages))
        self.assertIn("資料：持倉與現價已確認；風控由持倉成本/停損推算", position_message(messages))
        self.assertIn("新倉 RR：不適用（既有持倉）", position_message(messages))
        self.assertNotIn("Source：position available｜price available｜risk derived｜RR derived", position_message(messages))
        self.assertNotRegex(position_message(messages), r"數據：RR [0-9]")
        self.assertIn("資料：現價與 OHLCV 已確認；RR/分數/量能為模型推算", unheld_message(messages))
        self.assertNotIn("Source：price available｜OHLCV available｜RR derived｜score derived｜volume derived", unheld_message(messages))
        self.assertNotIn("Source：漏斗 count", summary_message(messages))
        self.assertIn("市場 / 題材背景：近 20 個交易日短期背景，近期 5 日支持仍支持目前背景觀察", evidence_message(messages))
        self.assertIn("策略樣本：本輪缺少可驗證樣本，可靠度低，未納入買賣判斷。", evidence_message(messages))
        self.assertIn("策略樣本：缺少可驗證來源，本次不納入買賣判斷。", evidence_message(messages))
        self.assertIn("持倉 RR：既有持倉若不是加碼情境，只顯示新倉 RR 不適用。", evidence_message(messages))
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
                    self.assertIn("策略樣本：缺少可驗證來源，本次不納入買賣判斷。", rendered)
                    self.assertIn("新倉：無有效進場。", rendered)
                    self.assertNotIn("建準｜可買", rendered)
                    self.assertNotIn("買點：可買", rendered)
                if case == "ledger_position_conflict":
                    self.assertIn("執行記憶：紀錄仍有待釐清的差異", rendered)
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
                self.assertEqual(report["generator_version"], "v20.4.21")
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
                self.assertIn("資料依據", report["telegram_messages"][2])
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
            strategy_evidence_summary=None,
            report_phase="盤中",
        )
        fields = {item["field_name"]: item for item in context["evidence_manifest"]}

        self.assertEqual(fields["stock.建準.price"]["source_status"], "insufficient-data")
        self.assertFalse(fields["stock.建準.price"]["decision_eligible"])
        self.assertEqual(fields["stock.建準.rr"]["source_status"], "insufficient-data")
        self.assertFalse(fields["stock.建準.rr"]["decision_eligible"])
        self.assertEqual(fields["funnel.unheld_counts"]["source_status"], "insufficient-data")
        self.assertEqual(fields["evidence.strategy_sample"]["source_status"], "missing-source")
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
            strategy_evidence_summary=None,
            report_phase="盤中",
        )
        joined = "\n\n".join(messages)
        summary = summary_message(messages)
        unheld = unheld_message(messages)

        self.assertIs(messages[2], summary)
        self.assertIn("【05/31 盤中｜v20.4.21】", summary)
        self.assertNotIn("Source：核心價格 insufficient-data", summary)
        self.assertIn("新倉：無有效進場", summary)
        self.assertIn("🔥 最強：無有效進場標的", summary)
        self.assertNotIn("🔥 最強：建準", summary)
        self.assertNotIn("排序★", summary)
        self.assertNotIn("評級★", summary)
        self.assertNotIn("交易執行 1", summary)
        self.assertIn("可買 0", summary)
        self.assertNotIn("Source：漏斗 count", summary)
        self.assertIn("【建準 2421】⛔ 不可行動｜source missing", unheld)
        self.assertIn("買點：不可買，source insufficient-data", unheld)
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
        self.assertIn("🔥 最強：無有效進場標的", summary)
        self.assertNotIn("🔥 最強：建準", summary)
        self.assertNotIn("排序★", summary)
        self.assertNotIn("評級★", summary)
        self.assertIn("買點：不可買，source missing-source", unheld)
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
        self.assertIn("🔥 最強：無有效進場標的", summary)
        self.assertNotIn("🔥 最強：建準", summary)
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

        self.assertIn("【建準 2421】⛔ 不可行動｜source missing", unheld)
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
            strategy_evidence_summary=None,
            report_phase="盤中",
        )
        summary = summary_message(messages)
        unheld = unheld_message(messages)
        invalid_card = unheld[unheld.index("【建準 2421】"):]
        invalid_card = invalid_card.split("\n\n【", 1)[0]

        self.assertIn("交易執行 1 項", summary)
        self.assertIn("光寶科｜可買｜分批，不追價", summary)
        self.assertNotIn("新倉：無有效進場", summary)
        self.assertIn("🔥 最強：光寶科", summary)
        self.assertIn("可買 1｜可準備 0（不可買）｜僅追蹤 0｜淘汰 1", summary)
        self.assertNotIn("Source：漏斗 count", summary)
        self.assertIn("【建準 2421】⛔ 不可行動｜source missing", invalid_card)
        self.assertIn("買點：不可買，source missing-source", invalid_card)
        self.assertIn("價格：不可用（source missing）", invalid_card)
        self.assertIn("數據：RR 不可用｜S 不可用｜V 不可用", invalid_card)
        self.assertNotIn("RR 2.1", invalid_card)
        self.assertNotIn("S 5/5", invalid_card)
        self.assertNotIn("V 1.5x", invalid_card)
        self.assertNotIn("價格：100", invalid_card)


if __name__ == "__main__":
    unittest.main()
