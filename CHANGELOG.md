# CHANGELOG: render_dispatch_writeback_logic_20260610

## Changes
- `app.py`
  - Added explicit Render timing constants.
  - Intraday dispatch buckets changed from 10 minutes to 5 minutes.
  - Close dispatch moved from `13:20..13:59` to `14:00..14:29`, aligning with market/theme `MARKET_THEME_SAFE_WRITE_TIME=14:00`.
  - GitHub dispatch now sends `{"inputs": {"run_mode": "bot"}}`.
- `.github/workflows/stock-bot-clean.yml`
  - Removed native GitHub cron schedule.
  - `RUN_MODE` now comes only from `workflow_dispatch` input or defaults to `bot`.
- `tests/test_app_render_preflight.py`
  - Added close-window regression: `13:25` skips, `14:05` dispatches after freshness.
  - Added five-minute intraday bucket regression.
  - Added explicit `run_mode=bot` dispatch payload regression.
- `tests/test_workflow_runtime_config.py`
  - Updated workflow contract to dispatch-only / no cron.

## Contract Impact
- Production timing is Render-driven, not GitHub cron-driven.
- Visible report version remains `v21.0.2`.
- No Telegram payload shape change.
- No DB schema change.

## Verification
- Render/workflow/phase3:
  ```powershell
  .\.venv\Scripts\python.exe -m pytest tests/test_app_render_preflight.py tests/test_workflow_runtime_config.py tests/test_phase3_evidence_automation.py -q --tb=short
  ```
  Result: `27 passed, 8 skipped`.

## Coverage Layers
- Render dispatch gate.
- GitHub workflow dispatch contract.
- Phase3 evidence helper path.

## Residual Risk
- Local workflow shell execution tests skipped because this machine's `bash` points to unavailable WSL/Hyper-V. Static workflow contract checks still passed.
- Live Render cron/ping execution is not proven locally; tests cover the Flask dispatch logic used by Render.
