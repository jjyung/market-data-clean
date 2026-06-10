# Week-1 Tasks: market-data-clean

This file contains your structured checklists for the first week of implementation. You can edit this file to mark items as completed (`[ ]` -> `[x]`).

## Task 1: Setup Development Environment

- [x] Create Python virtual environment (`python -m venv .venv`).
- [x] Install dependencies in development/editable mode (`uv pip install -e .` or `pip install -e .`).
- [x] Install test dependencies (`pytest`).
- [x] Run `pytest` to verify the smoke test passes.

```bash
uv add pytest
uv run pytest
```

## Task 2: Define Sample Input Format

- [ ] Create a sample CSV file under `examples/raw_data.csv` containing:
  - `symbol` (e.g., AAPL)
  - `timestamp` (e.g., 2026-06-01 09:30:00 or ISO8601 strings)
  - `open`, `high`, `low`, `close`, `volume`
- [ ] Include some intentionally malformed or duplicate rows to test validation.

## Task 3: Implement Parser

- [ ] Create `src/market_data_clean/parser.py`.
- [ ] Implement a function to parse the raw CSV into a pandas DataFrame or list of dicts.
- [ ] Ensure datetimes are parsed correctly.

## Task 4: Implement Validator

- [ ] Create `src/market_data_clean/validator.py`.
- [ ] Implement row-level validation (no negative prices/volume, high >= max(open, close), low <= min(open, close)).
- [ ] Implement dataset-level validation (detect duplicate `(symbol, timestamp)` rows).
- [ ] Separate rows into `cleaned` (passed all checks) and `rejected` (failed with a specific reason).

## Task 5: Implement CLI

- [ ] Update `src/market_data_clean/cli.py` to accept input path and output directory.
- [ ] Run the parser and validator on the input file.
- [ ] Write `cleaned.csv`, `rejected.csv`, and a brief `report.json` summarizing the run.

## Task 6: Add Tests

- [ ] Create tests under `tests/` verifying:
  - Valid rows are preserved.
  - Invalid rows are correctly rejected with the expected reason.
  - Duplicates are handled properly.

## Task 7: Run & Verify

- [ ] Run the pipeline against `examples/raw_data.csv`.
- [ ] Verify that `cleaned.csv`, `rejected.csv`, and `report.json` are written correctly.
