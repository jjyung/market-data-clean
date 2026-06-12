# Data Contract

## Purpose
Define the shape of raw and cleaned market data so the cleaning pipeline and downstream backtests stay consistent.

## Canonical cleaned schema
Required fields:
- `symbol`: string
- `timestamp`: timezone-aware datetime in UTC
- `open`: float
- `high`: float
- `low`: float
- `close`: float
- `volume`: integer

Optional fields:
- `adj_close`: float
- `source`: string
- `ingested_at`: timezone-aware datetime in UTC
- `governance.run_id`: string UUID linking a row to the pipeline run that produced it
- `source_version`: string identifying the source adapter/version (for example `sinopac:shioaji-1.5.2`)
- `adapter_trace`: stringified JSON provenance payload with source-record keys
- `quality_score`: float from `0.0` to `1.0` for lightweight row-level quality scoring

Governance fields are output-only and optional. Raw input adapters do not need to provide them.

## Rules
- All cleaned timestamps must be UTC.
- `open/high/low/close` must be numeric and non-negative.
- `high >= max(open, close)` and `low <= min(open, close)`.
- `volume` must be zero or positive.
- Duplicate `(symbol, timestamp)` rows are rejected unless a source-specific merge rule exists.

## Output sets
- `cleaned` — rows that pass validation
- `rejected` — rows that fail validation with reasons
- `report` — summary counts by rule and source

## Notes
If a raw source cannot map to this schema, it should be normalized in a source adapter before entering the cleaning core.
