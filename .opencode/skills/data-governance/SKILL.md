---
name: data-governance
description: |
  Bootstrap a lightweight DMBoK-aligned data governance foundation for batch data pipelines.
  Use when a project needs ownership, retention, lineage, audit, manifests, quality snapshots,
  or governance-aware data contracts. Triggers on: "data governance", "governance",
  "stewardship", "data lineage", "data quality", "retention policy", "audit trail",
  "run manifest", "data contract", "ownership", "DMBoK", "metadata management"
---

# Data Governance

Stand up a lightweight governance layer for a batch data pipeline without requiring an enterprise catalog or platform rollout first.

This skill is based on the governance patterns proven in this repo:
- version-controlled `governance.yaml`
- ownership and stewardship defaults + overrides
- retention policies by output category
- run manifests, quality snapshots, and append-only audit logs
- governance metadata added to data contracts and pipeline outputs

## When to Use

- Starting a new data pipeline and wanting governance from day one
- Upgrading an existing pipeline that lacks ownership, lineage, quality visibility, or retention rules
- Preparing for audit/compliance review of pipeline operations
- Codifying implicit governance decisions discovered during implementation or review
- Standardizing governance across multiple internal data projects

## When NOT to Use

- Pure frontend, mobile, or API-only projects with no batch data pipeline
- Projects already governed by an enterprise platform that owns these concerns end to end
- Real-time or event-stream governance rollouts where batch-run artifacts are the wrong abstraction
- Security/RBAC/encryption projects whose main problem is access control rather than data pipeline governance

## Trigger Phrases

- `data governance`
- `governance`
- `stewardship`
- `data lineage`
- `data quality`
- `retention policy`
- `audit trail`
- `run manifest`
- `data contract`
- `ownership`
- `DMBoK`
- `metadata management`

## Workflow Overview

```
Phase 0: Scout → Phase 1: Contract → Phase 2: Scaffold → Phase 3: Hook → Phase 4: Verify → Phase 5: Document
```

## Workflow Phases

### Phase 0: Scout

Goal: determine whether the target repo actually needs governance work and gather required inputs.

Steps:
1. Read project identity files (`pyproject.toml`, `package.json`, `Cargo.toml`)
2. Probe for pipeline entry points, adapters, and existing docs/contracts
3. Check for an existing repo-root `governance.yaml`
4. Ask for anything mandatory that cannot be inferred
5. Write a temporary scout handoff if active implementation is proceeding

Stop condition:
- If `governance.yaml` already exists, report that governance is already configured and do not overwrite it.

### Phase 1: Contract

Goal: define governance requirements before code changes.

Steps:
1. Create `docs/specs/data-governance/README.md`
2. Document sources, ownership, stewardship, retention, quality thresholds, and artifact expectations
3. Use RFC 2119 language (`MUST`, `SHOULD`, `MAY`)
4. Add GIVEN/WHEN/THEN acceptance criteria
5. Map requirements to the DMBoK MVP areas

Use template:
- `templates/governance-spec.md`

### Phase 2: Scaffold

Goal: establish a practical governance foundation with minimal moving parts.

MVP scaffold outputs:
- `governance.yaml` from `templates/governance.yaml`
- ownership/stewardship defaults and overrides
- retention categories: `raw_input`, `cleaned`, `rejected`, `report`, `manifest`
- quality thresholds and adapter version placeholders
- governance field additions for the project's data contract

For Python-first projects, scaffold toward this public surface:
- `load_config()`
- `build_manifest()`
- `build_quality_snapshot()`
- `append_audit_entry()`
- `build_ownership_map()`
- `collect_governance_warnings()`
- `build_retention_advisory()`

### Phase 3: Hook

Goal: wire governance into pipeline boundaries.

Typical integration points:
- before processing: load config, determine `run_id`, capture input stats
- during enrichment/output: add `governance.run_id`, `source_version`, optional `adapter_trace`, optional `quality_score`
- after writes: emit manifest, quality snapshot, audit log, config copy, retention advisory

Recommended CLI flags:
- `--governance-config`
- `--run-id`
- `--governance-output`
- `--no-governance`

Recommended subcommands:
- `governance init-config`
- `governance retention-check`

### Phase 4: Verify

Goal: confirm governance works and remains optional.

Verify at minimum:
- valid config loads
- invalid config fails clearly
- required retention categories exist
- audit log is append-only
- manifest / quality / audit artifacts are created when governance is enabled
- no governance artifacts are created when `--no-governance` is used

### Phase 5: Document

Goal: make governance discoverable for future maintainers.

Update:
- `README.md`
- `docs/data-contract.md`
- `docs/validation-rules.md` if present
- optional quickstart or governance operations notes

## Inputs to Gather

| Input | Required | Auto-detect | Notes |
|---|---|---:|---|
| Project name | Yes | Yes | From `pyproject.toml`, `package.json`, or `Cargo.toml` |
| Data sources | Yes | Partial | APIs, files, DBs, upstream services |
| Pipeline entry points | Yes | Partial | CLI, scripts, DAGs, main functions |
| Output categories | Yes | Partial | Must cover at least the governance retention set |
| Data domains | Yes | Partial | e.g. equities, futures, orders, telemetry |
| Existing data contracts/schemas | Yes | Partial | Docs, OpenAPI, Avro, Protobuf, validation docs |
| Environment | No | Partial | Default `development` |
| Data steward(s) | No | No | Email or team alias |
| Data owner(s) | No | No | Team or function owner |
| Retention defaults | No | No | Seed from repo pattern |
| Outlier fields | No | No | Numeric fields worth scanning |
| Adapter versions | No | Partial | Optional provenance enhancement |
| Language/runtime | No | Yes | Python is the MVP reference path |

## Concrete Outputs / Artifacts

| Phase | Output | Location | Persistent |
|---|---|---|---|
| 0 | Scout report | `.handoffs/data-governance/scout-report.json` | No |
| 1 | Governance spec | `docs/specs/data-governance/README.md` | Yes |
| 2 | Governance config | `governance.yaml` | Yes |
| 2 | Data contract fragment adoption | `docs/data-contract.md` | Yes |
| 3 | Pipeline hooks / CLI flags | project entry points | Yes |
| 4 | Verify report | `.handoffs/data-governance/verify-report.json` | No |
| 5 | Governance docs updates | `README.md`, docs | Yes |

Runtime artifacts expected after integration:
- `_governance/manifest.json`
- `_governance/quality.json`
- `_governance/audit_log.jsonl`
- `_governance/config_used.yaml`

## DMBoK MVP Mapping

| Area | Coverage | MVP Output |
|---|---|---|
| 1. Data Architecture | Light | pipeline scouting, entry-point inventory |
| 2. Data Modeling & Design | MVP | governance fields added to contracts/schemas |
| 3. Data Storage & Operations | MVP | retention policies + retention-check pattern |
| 4. Data Security | Out of scope | only optional `classification` tagging |
| 5. Data Integration & Interoperability | MVP | `source_version`, adapter provenance |
| 6. Document & Content Management | MVP | governance spec, README/docs updates |
| 7. Reference & Master Data | MVP | ownership/stewardship registry in `governance.yaml` |
| 8. Data Warehousing & BI | Out of scope | no warehouse/catalog rollout |
| 9. Metadata Management | MVP | manifests, audit logs, config snapshots |
| 10. Data Quality Management | MVP | thresholds, quality snapshots, warnings |

See also:
- `references/dmbok-mapping.md`

## Practical MVP Assets in This Skill

- `references/README.md` — index of reusable material
- `references/data-contract-fragment.md` — governance metadata fields to add to a data contract
- `templates/governance.yaml` — ready-to-copy governance config seed
- `templates/governance-spec.md` — project-level governance spec template
- `templates/implementation-checklist.md` — rollout checklist for execution and review

## Suggested Operating Pattern

1. Run `dev-flow` contract-first
2. Use this skill in Phase 0-1 to scout and define governance
3. Copy/adapt the templates in this skill
4. Implement language-specific hooks in the target repo
5. Use `test-gen` for governance test coverage
6. Use `docs-gen` for README and contract updates

## Related Skills / Delegation

- `dev-flow` — use for contract → code → verify workflow
- `adr` — use if the repo needs an explicit architectural decision to adopt governance
- `docs-gen` — use to update README, contracts, and governance docs
- `test-gen` — use to create/extend governance tests
- `orchestrate` — use for multi-repo governance rollout
- `pr-review` — use to review governance completeness and regressions

## Notes

- This skill is intentionally lightweight and batch-pipeline-first.
- It favors copyable templates and explicit checklists over heavy platform assumptions.
- If full automation is needed later, add scaffold scripts after the project proves the workflow.
