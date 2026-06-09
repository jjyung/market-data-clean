# Validation Rules

## Row-level checks
- required columns present
- timestamp parseable
- timestamp converted to UTC
- numeric fields parseable
- no negative prices
- no negative volume
- no impossible OHLC combinations

## Dataset-level checks
- duplicate key detection on `(symbol, timestamp)`
- ordering by symbol and timestamp
- gap detection for expected frequency when applicable
- rejected-row count and reason histogram

## Output requirements
The cleaner must produce:
- cleaned dataset
- rejected dataset with reason column
- summary report

## Acceptance criteria
A cleaning run is successful only if:
- the job completes without exception
- cleaned and rejected outputs are both written
- validation summary is emitted for inspection