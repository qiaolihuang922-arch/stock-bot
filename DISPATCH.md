# DISPATCH.md

## Active

- task_md_holds: `report_conflict_entry_gate_v21_0_5_20260615`
- status: `complete`
- owner_request:
  - Solve visible report conflicts.
  - Remove unreasonable blocker labels.
  - Check whether volume, market, heat, and low-point buying logic are reasonable.
  - No live Telegram delivery.

## Current Result

- Visible version is now `v21.0.5`.
- Broad market and individual-stock weakness are separated.
- A neutral market summary no longer turns every unheld stock into `等市場｜市場弱`.
- Real data/source failure is the only path that displays `等資料`.
- Heat, volume, RR, setup, and stock weakness are separate blockers.
- Current official dry-run emits no valid new buy; blocked names are wait/observe states, not recommendations.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_trade_state_machine.py tests/test_generator_report.py tests/test_market_theme_evidence.py -q --tb=short
```

Result: `246 passed, 145 warnings, 57 subtests passed`.

Official dry-run conflict probe:

```powershell
$env:PYTHONIOENCODING='utf-8'; .\.venv\Scripts\python.exe -c "from core.generator import generate_report, VERSION; messages,_=generate_report(dry_run=True); text='\n'.join(messages); print('version', VERSION); print('has_R2_market_weak_conflict', ('市場：中性觀察 R2' in text and '等市場｜市場弱' in text)); print('has_nextday_data_conflict', ('隔日確認' in text and '交易狀態：等資料' in text)); print('has_english_quality_noise', 'entry quality low' in text); print('has_buyable', '可買｜' in text or '趨勢延續買入' in text); print('liandian_rr', '【聯電 2303】👀 等RR修復｜觀察' in text and '交易狀態：等RR修復' in text)"
```

Result:
- `version v21.0.5`
- `has_R2_market_weak_conflict False`
- `has_nextday_data_conflict False`
- `has_english_quality_noise False`
- `has_buyable False`
- `liandian_rr True`

## Next Action

- Observe the next Render/GitHub scheduled report if external confirmation is needed.
