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

## Governance configuration validation
- governance config may be loaded from YAML or JSON
- invalid governance config aborts the run before file processing starts
- ownership overrides must include `symbol`, `source`, `data_steward`, `data_owner`, `criticality`, `classification`, `data_domain`, and `description`
- retention policies must define `category`, `retention_days`, `archive_after_days`, and `deletion_after_days`
- numeric retention values must be zero or positive; rejection-rate thresholds must be between `0.0` and `1.0`
- governance-enabled runs should emit validation/reporting artifacts including manifest, quality snapshot, audit log, and governance report sections

## Acceptance criteria
A cleaning run is successful only if:
- the job completes without exception
- cleaned and rejected outputs are both written
- validation summary is emitted for inspection
