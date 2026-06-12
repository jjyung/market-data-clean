# Data Governance Specification — {{project_name}}

## Context

{{project_name}} processes batch data from {{source_summary}} into {{output_summary}}.
This specification defines the minimum governance layer required for ownership,
retention, lineage, quality observability, and auditability.

## Requirements

### Data Sources

| Source | Version | Domain | Steward | Owner | Criticality |
|---|---|---|---|---|---|
| {{source_1}} | {{version_1}} | {{domain_1}} | {{steward_1}} | {{owner_1}} | {{criticality_1}} |

### Governance Requirements

- The pipeline MUST maintain a repo-root `governance.yaml`.
- The pipeline MUST define retention policies for `raw_input`, `cleaned`, `rejected`, `report`, and `manifest`.
- The pipeline MUST emit a run-level manifest and append-only audit entry when governance is enabled.
- Cleaned and rejected outputs SHOULD include `governance.run_id` and `source_version`.
- The project SHOULD emit a quality snapshot and governance warnings.
- The pipeline MAY expose `governance init-config` and `governance retention-check` entry points.

## Retention Policies

| Category | Retention Days | Archive After | Deletion After |
|---|---:|---:|---:|
| raw_input | 30 | 90 | 365 |
| cleaned | 365 |  |  |
| rejected | 90 | 180 | 365 |
| report | 730 |  |  |
| manifest | 730 |  |  |

## Quality Thresholds

- Outlier z-score: `3.0`
- Max rejection rate: `0.10`
- Outlier fields: `{{outlier_fields}}`

## DMBoK Alignment

- DMBoK-2 Data Modeling & Design — governance metadata fields and config shape
- DMBoK-3 Data Storage & Operations — retention policy definitions
- DMBoK-5 Data Integration & Interoperability — source and adapter provenance
- DMBoK-6 Document & Content Management — governance spec and docs updates
- DMBoK-7 Reference & Master Data — ownership and stewardship registry
- DMBoK-9 Metadata Management — manifests, config snapshots, audit logs
- DMBoK-10 Data Quality Management — thresholds, warnings, quality snapshots

## Acceptance Criteria

- GIVEN a valid governance-enabled run WHEN processing completes THEN `_governance/manifest.json` exists.
- GIVEN governance is enabled WHEN outputs are written THEN cleaned/rejected outputs include `governance.run_id` and `source_version`.
- GIVEN an invalid governance config WHEN the pipeline starts THEN processing aborts with a clear validation error.
- GIVEN governance is bypassed with `--no-governance` WHEN the pipeline runs THEN governance artifacts are not produced.

## Out of Scope

- enterprise data catalog integration
- automated archival or deletion
- RBAC / encryption / secrets controls
- streaming governance
