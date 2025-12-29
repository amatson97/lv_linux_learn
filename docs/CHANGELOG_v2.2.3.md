# Changelog v2.2.3 — Debug Logging Removal and UX Polish

Release Date: December 29, 2025  
Version: 2.2.3  
Focus: Remove verbose cache debug logging; keep behavior clean and consistent

---

## Summary

This patch release removes the temporary "CACHE-DEBUG" logging across the GUI and Python library modules. Runtime output is now quiet and focused on user-facing messages. Functional behavior remains the same, including auto-download and cache-first execution.

## Changes

- Removed CACHE-DEBUG prints in:
  - menu.py
  - lib/repository.py
  - lib/manifest_loader.py
  - lib/script_manager.py
  - lib/script_execution.py
- Preserved all functional behavior (no API changes)
- Kept repository operation logs in `~/.lv_linux_learn/logs/repository.log`

## Notes

- For troubleshooting, prefer checking the log file:
  - `tail -50 ~/.lv_linux_learn/logs/repository.log`
- The test harness remains available and passes:
  - `/home/adam/lv_linux_learn/.venv/bin/python tests/run_tests.py`

## Validation

- Test suite: 19 tests passed, 0 failures
- Manual run validations: GUI and CLI flows remain functional

## Next Steps

- Optional: bump `VERSION` to 2.2.3 and push
- Optional: expand logging to structured file-based logs if needed
