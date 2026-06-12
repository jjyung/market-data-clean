## Governance Metadata Fields

Append these fields to the project's existing cleaned-output data contract.

| Field | Type | Required | Description |
|---|---|---|---|
| `governance.run_id` | `string` | SHOULD | Unique identifier linking the row to a run manifest |
| `source_version` | `string` | SHOULD | Adapter/source version used to produce the row |
| `adapter_trace` | `object \| string \| null` | MAY | Source-system trace keys useful for replay/debugging |
| `quality_score` | `number \| null` | MAY | Row-level or record-level quality score between `0.0` and `1.0` |

## Contract language snippet

> Cleaned and rejected outputs SHOULD include governance metadata that links every produced record to a pipeline run, source adapter version, and optional diagnostic trace data.

## Report-level governance additions

Add these sections to `report.json` or equivalent run summary artifact:

- `ownership_map`
- `governance_warnings`
- `retention_advisory`
- `quality_summary`
- `governance_artifacts`

## Runtime artifact references

- `_governance/manifest.json`
- `_governance/quality.json`
- `_governance/audit_log.jsonl`
- `_governance/config_used.yaml`
