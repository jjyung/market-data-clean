## DMBoK Mapping — Lightweight Pipeline Governance MVP

This skill focuses on the smallest useful governance layer a delivery team can sustain inside a normal code repo.

| DMBoK Area | Coverage | What the MVP Does |
|---|---|---|
| Data Architecture | Light | inventories sources, entry points, and output boundaries |
| Data Modeling & Design | MVP | adds governance metadata fields and a governance config schema |
| Data Storage & Operations | MVP | defines retention policies and read-only retention checks |
| Data Security | Out of scope | does not implement RBAC, encryption, or secrets controls |
| Data Integration & Interoperability | MVP | preserves source provenance and adapter version context |
| Document & Content Management | MVP | generates governance specs and documentation updates |
| Reference & Master Data | MVP | treats ownership/stewardship config as lightweight reference data |
| Data Warehousing & BI | Out of scope | no warehouse, semantic layer, or BI modeling |
| Metadata Management | MVP | emits manifests, snapshots, audit logs, and config copies |
| Data Quality Management | MVP | sets thresholds, warnings, and quality summary expectations |

## MVP principles

1. Governance is code-adjacent, version-controlled, and reviewable.
2. Governance is advisory-first; avoid destructive automation in the first pass.
3. Lineage must be cheap enough to keep turned on.
4. Ownership must be explicit, even if defaults are initially broad.
5. Quality observability should produce artifacts, not just console output.

## Explicit non-goals

- enterprise metadata catalogs
- automated archival/deletion jobs
- PII detection or access control frameworks
- cross-dataset lineage graphs
- warehouse or BI governance programs
