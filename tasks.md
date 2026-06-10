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

## Task 2: API Source Survey & Unified Input Format

- [x] Document 永豐 API (Sinopac) futures real-time quote format → `docs/api-sources/sinopac.md`
  - [x] Tick (逐筆成交明細) — `TickFOPv1`
  - [x] BidAsk (五檔委買委賣) — `BidAskFOPv1`
  - [x] Quote (綜合報價) — `QuoteFOPv1`
  - [x] Adapter mapping to unified format
- [x] Document FinMind API futures data format → `docs/api-sources/finmind.md`
  - [x] TaiwanFuturesDaily (盤後日成交資訊)
  - [x] TaiwanFuturesTick (歷史逐筆明細)
  - [x] taiwan_futures_snapshot (即時快照)
  - [x] Adapter mapping to unified format
- [x] Define unified raw input contract → `docs/api-sources/raw-input-contract.md`
  - [x] OHLCV Pipeline (主) — 支援期貨日資料與即時報價
  - [x] OrderBook Pipeline (輔) — 五檔報價獨立處理
  - [x] API-to-unified mapping table for both sources
  - [x] Timezone normalization rules
- [ ] Create a sample CSV file under `examples/raw_data.csv` in the unified format
  - [ ] Include futures data rows from different sources (`source` column)
  - [ ] Include intentionally malformed or duplicate rows to test validation

```bash
uv add shioaji
```

## Task 3: Implement Source Adapters

- [ ] Create `src/market_data_clean/adapters/`.
- [ ] Implement `sinopac.py` adapter for **期貨即時成交 / quote** → unified OHLCV format.
  - [ ] Support `TickFOPv1` / `QuoteFOPv1` normalization.
  - [ ] Normalize `date + time` into UTC `timestamp`.
  - [ ] Map `Decimal` fields into Python numeric types.
- [ ] Implement `finmind.py` adapter for **期貨日資料 / snapshot** → unified OHLCV format.
  - [ ] Support `TaiwanFuturesDaily` normalization.
  - [ ] Support `taiwan_futures_snapshot` normalization.
- [ ] Defer `BidAskFOPv1` / order book pipeline to a later phase.

## Task 4: Implement Parser

- [ ] Create `src/market_data_clean/parser.py`.
- [ ] Implement parser entrypoints for:
  - [ ] unified CSV input
  - [ ] list of dicts / DataFrame input from adapters
- [ ] Ensure datetimes are parsed as timezone-aware UTC.
- [ ] Validate required unified fields are present before entering validator.

## Task 5: Implement Validator

- [ ] Create `src/market_data_clean/validator.py`.
- [ ] Implement row-level validation for **OHLCV pipeline**:
  - [ ] no negative prices / volume
  - [ ] `high >= max(open, close)`
  - [ ] `low <= min(open, close)`
- [ ] Implement dataset-level validation:
  - [ ] detect duplicate `(symbol, timestamp)` rows
  - [ ] report missing required fields
- [ ] Separate rows into `cleaned` (passed all checks) and `rejected` (failed with a specific reason).
- [ ] Keep order book validation out of MVP for now.

## Task 6: Implement CLI

- [ ] Update `src/market_data_clean/cli.py` to accept input path and output directory.
- [ ] Support running the cleaner against `examples/raw_data.csv` in unified format.
- [ ] Run parser and validator on the input data.
- [ ] Write `cleaned.csv`, `rejected.csv`, and `report.json`.

## Task 7: Add Tests

- [ ] Create tests under `tests/` verifying:
  - [ ] valid unified OHLCV rows are preserved
  - [ ] invalid rows are rejected with the expected reason
  - [ ] duplicate `(symbol, timestamp)` rows are handled properly
  - [ ] adapter outputs match the unified contract

## Task 8: Run & Verify

- [ ] Run the pipeline against `examples/raw_data.csv`.
- [ ] Verify that `cleaned.csv`, `rejected.csv`, and `report.json` are written correctly.
- [ ] Confirm the sample data only covers **加權指數期貨 / 小台指期貨** scope.
