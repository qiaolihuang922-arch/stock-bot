from presentation.report import _unheld_buy_gap_line


def test_unheld_quality_gap_includes_setup_volume_and_rr_context():
    data = {
        "price": 161.5,
        "volume_ratio": 0.48,
        "volume_ratio_10": 0.48,
        "volume_ratio_20": 0.61,
        "retest_zone_low": 194,
        "retest_zone_high": 194.97,
        "result": {
            "entry_quality": "D",
            "rr": 9.94,
        },
    }

    line = _unheld_buy_gap_line(
        data,
        dist=20.72,
        blockers=[],
        valid_entry=False,
        funnel_state="等型態",
        source_status="available",
        strategy_source_blocked=False,
    )

    assert "不能買：型態/品質還沒過" in line
    assert "品質 D→B以上" in line
    assert "站回突破區 194~194.97" in line
    assert "量能偏弱（V10 0.48x / V20 0.61x）" in line
    assert "理論RR 9.94僅參考" in line


def test_unheld_rebound_gap_keeps_retest_unlock_contract():
    data = {
        "price": 159,
        "volume_ratio": 0.52,
        "volume_ratio_10": 0.52,
        "volume_ratio_20": 0.26,
        "retest_zone_low": 175.5,
        "retest_zone_high": 176.38,
        "result": {
            "entry_quality": "D",
            "rr": 2.21,
        },
    }

    line = _unheld_buy_gap_line(
        data,
        dist=10.93,
        blockers=["急彈待回測"],
        valid_entry=False,
        funnel_state="等回測",
        source_status="available",
        strategy_source_blocked=False,
    )

    assert "不能買：急彈後還沒回測確認" in line
    assert "急彈後先等回測" in line
    assert "站回突破區 175.5~176.38" in line
    assert "量能偏弱（V10 0.52x / V20 0.26x）" in line
    assert "品質 D→B以上" in line
    assert "理論RR 2.21僅參考" in line
    assert "先站回突破區 175.5~176.38，再回測不破" in line
