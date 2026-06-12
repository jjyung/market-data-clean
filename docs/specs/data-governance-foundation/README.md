# Data Governance Foundation — First Pass

## 1. Feature Title & Context

**Feature:** `data-governance-foundation`

**Context:**

This repository normalises and validates Taiwan futures market data (TX / MTX; TAIFEX) from two sources — Sinopac (real-time tick/quote) and FinMind (historical daily/tick/snapshot) — into a canonical cleaned schema consumed by downstream research and backtesting.

The current documented pipeline is:

```
Source API → Adapter → Unified Raw Input → Parser → Validator → Cleaned / Rejected / Report
```

The existing contracts (`docs/data-contract.md`, `docs/validation-rules.md`, `docs/api-sources/raw-input-contract.md`) define *what* the data looks like and *which* rules it must pass, but they do **not** address:

- **Provenance / lineage** — Where did each row come from, when, via which adapter?
- **Quality observability** — How clean is a dataset? How do quality metrics trend over runs?
- **Ownership & stewardship** — Who is responsible for each symbol, source, or pipeline stage?
- **Retention & lifecycle** — How long do we keep raw, cleaned, and rejected data?
- **Auditability** — Can we replay or explain any cleaning run?

This spec defines the first-pass data governance layer that adds these capabilities **without** re-architecting the existing pipeline. Governance metadata is injected at the adapter and validator boundaries; lineage and quality records are emitted as sidecar artifacts.

---

## 2. DAMA DMBoK Alignment

This section maps the first-pass governance foundation scope to the ten **DAMA DMBoK (Data Management Body of Knowledge)** knowledge areas. Each area is classified by MVP coverage:

| Classification | Meaning |
|---|---|
| **🎯 MVP Focus** | Directly addressed by first-pass implementation. Concrete artifacts, config, or code changes planned. |
| **🔶 Lightly Addressed** | Foundational structures exist (contract, config field, or pipeline pattern) but deep capabilities deferred. |
| **⏭️ Out of Scope (MVP)** | Deliberately excluded from first pass. No design or implementation work planned. |

### 2.1 DMBoK Area Mapping

| # | Knowledge Area | Classification | How This Spec Addresses It |
|---|---|---|---|
| 1 | **Data Architecture** | 🔶 Lightly Addressed | Pipeline architecture is documented (adapter → parser → validator → cleaned/rejected/report). Governance artifacts extend the architecture with lineage and observability layers (§5–§6). A full enterprise data architecture framework (catalog, data mesh, bus) is out of scope. |
| 2 | **Data Modeling and Design** | 🎯 MVP Focus | Canonical cleaned schema (`docs/data-contract.md`), raw input contract (`docs/api-sources/raw-input-contract.md`), and governance metadata fields (`governance.run_id`, `source_version`, `adapter_trace`, `quality_score`) define the data models. Config models (`GovernanceConfig`, `RunManifest`, `QualitySnapshot`) are Pydantic/dataclass-defined (§6). |
| 3 | **Data Storage and Operations** | 🎯 MVP Focus | Retention policies defined per output category (`raw_input`, `cleaned`, `rejected`, `report`, `manifest`) with retention/archive/deletion timelines. Retention advisory engine scans and reports expired files (§3.4, §4 AC-7). Automated archival/deletion is explicitly advisory-only. |
| 4 | **Data Security** | ⏭️ Out of Scope (MVP) | Taiwan futures OHLCV data contains no PII. RBAC, encryption-at-rest, access control lists, and secrets management are deployment-environment concerns, not addressed in this batch pipeline library. A `classification` field is added to governance config (§6.1) for future security tagging. |
| 5 | **Data Integration and Interoperability** | 🎯 MVP Focus | Adapter pattern (Sinopac ↔ FinMind → unified raw input) is core to the repo. The raw input contract (§1) defines a canonical interchange format. Governance adds `source_version` and `adapter_trace` (§6.2) to preserve source-system provenance across integration boundaries. |
| 6 | **Document and Content Management** | 🎯 MVP Focus | Governance artifacts (manifests, quality snapshots, audit logs — §5.3) are versioned, immutable documents stored alongside pipeline outputs. Existing API source documentation (`docs/api-sources/sinopac.md`, `finmind.md`, `raw-input-contract.md`) covers content management. |
| 7 | **Reference and Master Data Management** | 🎯 MVP Focus | `governance.yaml` (§6.1) defines a symbol-source registry with ownership, stewardship, criticality, description, and `data_domain` for each (`symbol`, `source`) pair. This is a lightweight reference data layer — a master-data golden record for market-data symbols. |
| 8 | **Data Warehousing and Business Intelligence** | ⏭️ Out of Scope (MVP) | This is a data cleaning library, not a warehouse or BI platform. Downstream backtesting and research (which consume cleaned data) may implement their own warehousing; that is outside this repo's scope. |
| 9 | **Metadata Management** | 🎯 MVP Focus | Lineage (`run_id`, `source_version`, `adapter_trace` — §3.1), run manifests (input hash, cli version, timestamps — §5.3.1), adapter version tracking (§6.1), and append-only audit logs (§3.5, §5.3.3) provide operational metadata management. A searchable metadata catalog (e.g., Apache Atlas, DataHub) is out of scope (§8). |
| 10 | **Data Quality Management** | 🎯 MVP Focus | The validator rejects rows against defined rules (§3.2). The quality snapshot (`quality.json`) captures per-rule/per-source breakdowns, null counts, and outlier flags (§5.3.2). The report includes rejection rate and per-source quality metrics (§5.3.4). Quality thresholds are configurable (§6.1). |

### 2.2 Coverage Summary

```
🎯 MVP Focus (7):    Data Modeling & Design,
                     Data Storage & Operations,
                     Data Integration & Interoperability,
                     Document & Content Management,
                     Reference & Master Data Management,
                     Metadata Management,
                     Data Quality Management

🔶 Lightly Addressed (1):  Data Architecture

⏭️ Out of Scope (2):  Data Security,
                     Data Warehousing & Business Intelligence
```

### 2.3 How This Section Is Used

Every subsequent section in this spec references DMBoK area numbers in parentheses — e.g., `[DMBoK-2]` for Data Modeling & Design. This makes it explicit which knowledge area each requirement, acceptance criterion, or artifact serves. Implementation phases also note which DMBoK areas they primarily advance.

---

## 3. Requirements (RFC 2119)

### 3.1 Lineage & Provenance [DMBoK-9: Metadata Management]

| ID | Requirement | Priority | DMBoK Area |
|---|---|---|---|
| GOV-LIN-01 | Every cleaning run MUST produce a **run manifest** containing `run_id`, `started_at`, `finished_at`, `cli_version`, `adapter_versions`, and `input_source_hash`. | MUST | DMBoK-9 |
| GOV-LIN-02 | Every row in the `cleaned` and `rejected` output sets MUST carry a `governance.run_id` reference linking back to the manifest. | MUST | DMBoK-9 |
| GOV-LIN-03 | The `source` field (already required by the raw input contract) MUST be supplemented by `source_version` (e.g. `"sinopac:shioaji-1.5.2"` or `"finmind:api-v4"`). | MUST | DMBoK-5, DMBoK-9 |
| GOV-LIN-04 | Each adapter SHOULD emit an `adapter_trace` field with the original source record keys so a specific tick or daily record can be traced to its API response. | SHOULD | DMBoK-9 |
| GOV-LIN-05 | The manifest SHOULD include `git_commit_hash` of the codebase at run time. | SHOULD | DMBoK-9 |

### 3.2 Quality Observability [DMBoK-10: Data Quality Management]

| ID | Requirement | Priority | DMBoK Area |
|---|---|---|---|
| GOV-QAL-01 | The cleaning report MUST include a **quality summary** section with: total rows, accepted rows, rejected rows, rejection rate (%), per-rule rejection counts, and per-source rejection counts. | MUST | DMBoK-10 |
| GOV-QAL-02 | Each rejected row MUST carry a `rejection_reasons` field (already in the contract; MUST be a `list[str]`, one per failed rule). | MUST | DMBoK-10 |
| GOV-QAL-03 | The pipeline SHOULD emit a **quality snapshot** artifact (`quality.json`) alongside the report, containing pass/fail histograms, per-field null counts, and outlier flags for numeric fields. | SHOULD | DMBoK-10 |
| GOV-QAL-04 | The pipeline MAY compute and emit **row-level quality score** (`0.0`–`1.0`) based on completeness and rule-pass rate, stored in a `quality_score` field on the canonical schema. | MAY | DMBoK-10 |
| GOV-QAL-05 | The quality snapshot SHOULD be timestamped and immutable (written once, never overwritten). | SHOULD | DMBoK-10 |

### 3.3 Ownership & Stewardship [DMBoK-7: Reference & Master Data Management]

| ID | Requirement | Priority | DMBoK Area |
|---|---|---|---|
| GOV-OWN-01 | A **governance configuration file** MUST define ownership and stewardship metadata for each `source` and `symbol`. | MUST | DMBoK-7 |
| GOV-OWN-02 | The governance config MUST support at minimum: `symbol`, `source`, `data_steward` (email), `data_owner` (team name), `criticality` (`low`/`medium`/`high`), `classification`, `data_domain`, and `description`. | MUST | DMBoK-7 |
| GOV-OWN-03 | The cleaning report SHOULD include an ownership section mapping sources and symbols to their stewards. | SHOULD | DMBoK-7 |
| GOV-OWN-04 | The pipeline SHOULD validate that all symbols/sources appearing in input data have a corresponding entry in the governance config; entries without ownership SHOULD produce a warning in the report. | SHOULD | DMBoK-7 |

### 3.4 Retention & Data Lifecycle [DMBoK-3: Data Storage & Operations]

| ID | Requirement | Priority | DMBoK Area |
|---|---|---|---|
| GOV-RET-01 | Each output category (`raw_input`, `cleaned`, `rejected`, `report`, `manifest`) MUST have a **retention policy** defined in the governance configuration. | MUST | DMBoK-3 |
| GOV-RET-02 | A retention policy MUST specify: `category`, `retention_days`, `archive_after_days` (nullable), and `deletion_after_days`. | MUST | DMBoK-3 |
| GOV-RET-03 | The pipeline SHOULD emit a **retention advisory** section in the report listing files eligible for archival or deletion based on the policy. | SHOULD | DMBoK-3 |
| GOV-RET-04 | The CLI MAY gain a `governance retention-check` subcommand that lists expired artifacts without running the cleaning pipeline. | MAY | DMBoK-3 |

### 3.5 Audit Trail [DMBoK-9: Metadata Management]

| ID | Requirement | Priority | DMBoK Area |
|---|---|---|---|
| GOV-AUD-01 | Every cleaning run MUST produce an **audit entry** (appended to `audit_log.jsonl`) containing: `run_id`, `timestamp`, `input_path`, `output_dir`, `num_input_rows`, `num_cleaned`, `num_rejected`, `version`, `user` (from `$USER` or config). | MUST | DMBoK-9 |
| GOV-AUD-02 | The audit log MUST be append-only; the pipeline MUST NOT modify or delete existing audit entries. | MUST | DMBoK-9 |
| GOV-AUD-03 | The audit log SHOULD be stored alongside the governance config (default: `<output_dir>/_governance/audit_log.jsonl`). | SHOULD | DMBoK-9 |

### 3.6 Configuration [DMBoK-7: Reference & Master Data Management]

| ID | Requirement | Priority | DMBoK Area |
|---|---|---|---|
| GOV-CFG-01 | Governance configuration MUST be loadable from a YAML or JSON file specified via CLI flag or default path `<repo_root>/governance.yaml`. | MUST | DMBoK-7 |
| GOV-CFG-02 | The configuration MUST be validated at pipeline start; invalid config MUST abort the run with a clear error message listing the violations. | MUST | DMBoK-7 |
| GOV-CFG-03 | The pipeline SHOULD provide a `governance init-config` command that writes a default `governance.yaml` template. | SHOULD | DMBoK-7 |

---

## 4. Acceptance Criteria (GIVEN / WHEN / THEN)

### AC-1: Run manifest is produced [DMBoK-9: Metadata Mgmt]

```
GIVEN a valid input dataset in unified raw format
 WHEN the cleaning pipeline runs to completion
 THEN a file `<output_dir>/_governance/manifest.json` is written
  AND it contains `run_id`, `started_at`, `finished_at`, `cli_version`, and `input_source_hash`
```

### AC-2: Lineage fields on every output row [DMBoK-9: Metadata Mgmt]

```
GIVEN a row passes validation
 WHEN it is written to `cleaned.csv`
 THEN the row includes `governance.run_id` and `source_version` fields
```

### AC-3: Quality summary in report [DMBoK-10: Data Quality Mgmt]

```
GIVEN a cleaning run with mixed valid and invalid rows
 WHEN the `report.json` is generated
 THEN it contains a `quality_summary` section with:
  - total_rows (integer)
  - accepted_rows (integer)
  - rejected_rows (integer)
  - rejection_rate (float, 0.0–1.0)
  - rules_broken (object mapping rule-name -> count)
  - per_source_rejection (object mapping source -> {total, rejected})
```

### AC-4: Unowned symbol warning [DMBoK-7: Reference & Master Data]

```
GIVEN an input dataset contains symbol "TXFR1"
  AND the governance configuration has no entry matching "TXFR1"
 WHEN the pipeline runs
 THEN `report.json` contains a `governance_warnings` array
  AND one warning includes "TXFR1" and "no ownership entry found"
```

### AC-5: Governance config validation failure [DMBoK-7: Reference & Master Data]

```
GIVEN a governance configuration with an invalid field (e.g. `retention_days: -1`)
 WHEN the pipeline is invoked
 THEN the pipeline aborts before processing data
  AND a clear error message is printed naming the invalid field and value
```

### AC-6: Audit log append [DMBoK-9: Metadata Mgmt]

```
GIVEN two consecutive cleaning runs on different input files
 WHEN both runs complete successfully
 THEN `<output_dir>/_governance/audit_log.jsonl` contains two JSON lines
  AND each line has a unique `run_id`
```

### AC-7: Retention advisory [DMBoK-3: Storage & Operations]

```
GIVEN a governance config defines `retention_days: 30` for `raw_input`
  AND an input file is older than 30 days
 WHEN the pipeline runs
 THEN `report.json` includes a `retention_advisory` section
  AND it lists the expired file path with `days_overdue: N`
```

### AC-8: Ownership info in report [DMBoK-7: Reference & Master Data]

```
GIVEN a governance config with an ownership entry for source "sinopac"
 WHEN the pipeline finishes
 THEN `report.json` contains an `ownership_map` object
  AND it includes the steward and owner for "sinopac"
```

---

## 5. API / CLI Contract Changes

### 5.1 Current CLI

```bash
market-data-clean --input <path> --output <dir>
# Produces: <output>/cleaned.csv, <output>/rejected.csv, <output>/report.json
```

### 5.2 Proposed CLI Additions

All additions are **optional** — the pipeline MUST work without any governance flags, emitting only core outputs (backward-compatible).

#### Flags

| Flag | Type | Default | Description |
|---|---|---|---|
| `--governance-config` | `str` (path) | `./governance.yaml` | Path to governance YAML/JSON configuration. If file does not exist, governance features are silently skipped (no ownership, retention checks). |
| `--run-id` | `str` | Auto-generated UUID v4 | Explicit run identifier for traceability. Auto-generated if not provided. |
| `--governance-output` | `str` (path) | `<output>/_governance/` | Directory for governance artifacts (manifest, audit log, quality snapshot). |
| `--no-governance` | `flag` | `false` | Explicitly disable all governance features even if config file exists. |

#### New Subcommands

| Subcommand | Purpose |
|---|---|
| `market-data-clean governance init-config` | Write a default `governance.yaml` template to stdout or specified path (`--output`). Exits 0 on success. |
| `market-data-clean governance retention-check --config <path> --data-dir <path>` | Scan data directory against retention policy and print expired files. Does **not** delete or modify files. Exits 0 if nothing expired, 1 if any are expired. |

### 5.3 Output Artifact Contract

All governance artifacts are written under `<output>/_governance/` (configurable via `--governance-output`).

| Artifact | File | Format | Written When |
|---|---|---|---|
| **Run Manifest** | `manifest.json` | JSON | Always, if governance enabled |
| **Quality Snapshot** | `quality.json` | JSON | Always, if governance enabled |
| **Audit Log** | `audit_log.jsonl` | JSON Lines (append) | Always, if governance enabled |
| **Governance Config Copy** | `config_used.yaml` | YAML/JSON (mirror input) | Always, if governance enabled |

#### 5.3.1 `manifest.json` Structure

```jsonc
{
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "cli_version": "0.1.0",
  "git_commit_hash": "a1b2c3d",
  "started_at": "2026-06-12T08:00:00Z",
  "finished_at": "2026-06-12T08:00:05Z",
  "input": {
    "path": "/data/raw/2026-06-12-input.csv",
    "num_rows": 15000,
    "sha256": "e3b0c44298fc1c149afbf4c8996fb924..."
  },
  "adapter_versions": {
    "sinopac": "shioaji-1.5.2",
    "finmind": "finmind-api-v4"
  },
  "output": {
    "cleaned_rows": 14200,
    "rejected_rows": 800,
    "output_path": "/data/cleaned/2026-06-12/"
  }
}
```

#### 5.3.2 `quality.json` Structure

```jsonc
{
  "run_id": "<uuid>",
  "generated_at": "2026-06-12T08:00:05Z",
  "summary": {
    "total_rows": 15000,
    "accepted_rows": 14200,
    "rejected_rows": 800,
    "rejection_rate": 0.0533
  },
  "per_rule_breakdown": {
    "required_fields_missing": 120,
    "negative_price": 45,
    "high_lt_max_open_close": 200,
    "low_gt_min_open_close": 180,
    "duplicate_symbol_timestamp": 80,
    "unparseable_timestamp": 30,
    "non_numeric_field": 145
  },
  "per_source_breakdown": {
    "sinopac": { "total": 10000, "accepted": 9600, "rejected": 400 },
    "finmind": { "total": 5000, "accepted": 4600, "rejected": 400 }
  },
  "field_null_counts": {
    "open": 0,
    "high": 2,
    "low": 1,
    "close": 0,
    "volume": 0,
    "amount": 3500,
    "source_version": 0
  },
  "outlier_flags": {
    "volume": { "z_score_threshold": 3.0, "flagged_rows": 12 },
    "close": { "z_score_threshold": 3.0, "flagged_rows": 5 }
  }
}
```

#### 5.3.3 `audit_log.jsonl` (append-only)

Each line is a JSON object; one per run:

```json
{"run_id":"<uuid>","timestamp":"2026-06-12T08:00:05Z","input_path":"/data/raw/2026-06-12-input.csv","output_dir":"/data/cleaned/2026-06-12/","num_input_rows":15000,"num_cleaned":14200,"num_rejected":800,"cli_version":"0.1.0","user":"cfh00902455"}
```

#### 5.3.4 Enhancement to `report.json` (existing artifact)

Add a `governance` top-level key to the existing cleaning report:

```jsonc
{
  // ... existing fields (summary, rule_counts, etc.) ...
  "governance": {
    "run_id": "<uuid>",
    "manifest_path": "_governance/manifest.json",
    "ownership_map": {
      "sinopac": {
        "steward": "trading-team@example.com",
        "owner": "Quant Research"
      },
      "finmind": {
        "steward": "data-engineering@example.com",
        "owner": "Data Platform"
      }
    },
    "governance_warnings": [
      "symbol 'TXFR2' has no ownership entry in governance config"
    ],
    "retention_advisory": {
      "expired_artifacts": [
        {
          "category": "raw_input",
          "path": "/data/raw/old-import.csv",
          "age_days": 95,
          "policy_days": 30,
          "days_overdue": 65,
          "action": "archive_or_delete"
        }
      ]
    }
  }
}
```

---

## 6. Data Model Changes

### 6.1 Governance Configuration Schema — `governance.yaml`

```yaml
# ==============================================================
# Data Governance Configuration — market-data-clean
# ==============================================================
# DAMA DMBoK alignment: Ownership (DMBoK-7), Retention (DMBoK-3),
# Adapter tracking (DMBoK-9), Quality thresholds (DMBoK-10)
# ==============================================================
version: "1.0"

metadata:
  project: "market-data-clean"
  environment: "development"            # development / staging / production
  created_at: "2026-06-12T00:00:00Z"
  updated_at: "2026-06-12T00:00:00Z"

# ------------------------------------------------------------------
# Ownership & Stewardship                       [DMBoK-7: Reference & Master Data]
# ------------------------------------------------------------------
ownership:
  defaults:
    data_steward: "data-team@example.com"
    data_owner: "Quant Research"
    criticality: "medium"
    classification: "internal"          # public | internal | confidential | restricted
    data_domain: "futures"              # data domain for reference data grouping
  overrides:
    - symbol: "TXFR1"
      source: "sinopac"
      data_steward: "trading-desk@example.com"
      data_owner: "Execution Team"
      criticality: "high"
      classification: "internal"
      data_domain: "futures"
      description: "TX front-month real-time tick — trading-critical"
    - symbol: "TX"
      source: "finmind"
      data_steward: "data-engineering@example.com"
      data_owner: "Data Platform"
      criticality: "medium"
      classification: "internal"
      data_domain: "futures"
      description: "TX daily OHLCV from FinMind — research use"
    - symbol: "MTX"
      source: "finmind"
      data_steward: "data-engineering@example.com"
      data_owner: "Data Platform"
      criticality: "medium"
      classification: "internal"
      data_domain: "futures"
      description: "MTX daily OHLCV from FinMind — research use"

# ------------------------------------------------------------------
# Data Quality Thresholds                      [DMBoK-10: Data Quality Management]
# ------------------------------------------------------------------
# These thresholds govern quality snapshot computation and report
# flagging. They are advisory — the pipeline never drops data based
# on these values.
# ------------------------------------------------------------------
quality:
  outlier_z_score: 3.0                  # Z-score threshold for numeric outlier detection
  max_rejection_rate: 0.10              # If actual > this, report flags a quality alert
  outlier_fields:                       # Fields to scan for outliers in quality.json
    - "volume"
    - "close"

# ------------------------------------------------------------------
# Retention Policies                         [DMBoK-3: Data Storage & Operations]
# ------------------------------------------------------------------
retention:
  policies:
    - category: "raw_input"
      retention_days: 30
      archive_after_days: 90
      deletion_after_days: 365
    - category: "cleaned"
      retention_days: 365
      archive_after_days: null        # never archived separately
      deletion_after_days: null       # kept indefinitely
    - category: "rejected"
      retention_days: 90
      archive_after_days: 180
      deletion_after_days: 365
    - category: "report"
      retention_days: 730
      archive_after_days: null
      deletion_after_days: null
    - category: "manifest"
      retention_days: 730
      archive_after_days: null
      deletion_after_days: null

# ------------------------------------------------------------------
# Adapter Versions                         [DMBoK-9: Metadata Management]
# (declared, compared at runtime for version consistency)
# ------------------------------------------------------------------
adapters:
  sinopac:
    expected_version: "shioaji-1.5.2"
    source_label: "sinopac"
  finmind:
    expected_version: "finmind-api-v4"
    source_label: "finmind"
```

### 6.2 Governance Metadata Fields — Canonical Schema Additions

Add the following **optional** governance fields to the canonical cleaned schema (`docs/data-contract.md` must be updated):

| Field | Type | Required | Description |
|---|---|---|---|
| `governance.run_id` | `string` (UUID) | No | Links each row to the pipeline run that produced it |
| `source_version` | `string` | No | Source + adapter version, e.g. `"sinopac:shioaji-1.5.2"` |
| `adapter_trace` | `string` (JSON) | No | Original source record keys for provenance tracing |
| `quality_score` | `float` (0.0–1.0) | No | Row-level quality score based on completeness and rule pass rate |

These fields are output-only (added during pipeline processing) and NOT required from raw input adapters.

### 6.3 Governance Entity Summary

| Entity | DMBoK | Storage | Description |
|---|---|---|---|
| `RunManifest` | DMBoK-9 | `manifest.json` | Single JSON object per run; immutable. Contains run_id, timestamps, input/output stats, adapter versions, git hash. |
| `QualitySnapshot` | DMBoK-10 | `quality.json` | Single JSON object per run; immutable. Contains per-rule/per-source breakdowns, null counts, outlier flags. |
| `QualityConfig` | DMBoK-10 | `governance.yaml` (quality section) | Thresholds for outlier detection (z-score), max rejection rate, outlier field list. Loaded from governance config, used by quality snapshot builder. |
| `AuditEntry` | DMBoK-9 | `audit_log.jsonl` | Append-only JSON Lines file. One entry per run with summary stats. |
| `GovernanceConfig` | DMBoK-7, DMBoK-3 | `governance.yaml` | Source-of-truth config file. Owned by the project, version-controlled. Contains ownership, retention, quality thresholds, adapter versions. |
| `OwnershipEntry` | DMBoK-7 | `governance.yaml` (ownership.overrides) | Per-symbol-source steward, owner, criticality, classification, data_domain. |
| `DataProductLineage` | DMBoK-7, DMBoK-9 | `report.json` (governance key) | Run-time computed ownership map and retention advisory attached to the existing cleaning report. |

---

## 7. Affected Files

### 7.1 Existing Files (to be modified)

| File | Change | DMBoK |
|---|---|---|
| `src/market_data_clean/cli.py` | Add `--governance-config`, `--run-id`, `--governance-output`, `--no-governance` flags; add `governance` subcommand group with `init-config` and `retention-check`. | — |
| `docs/data-contract.md` | Add optional governance metadata fields to canonical schema (`governance.run_id`, `source_version`, `adapter_trace`, `quality_score`). | DMBoK-2 |
| `docs/validation-rules.md` | Add governance configuration validation rules (config schema, field ranges). | DMBoK-10 |
| `pyproject.toml` | Add `pyyaml` dependency for YAML config parsing. | — |

### 7.2 Existing Files (no change, but governance consumes)

| File | Relation |
|---|---|
| `src/market_data_clean/validator.py` | (Not yet created) — Must emit governance-quality stats and collect per-rule/per-source counts. |
| `src/market_data_clean/adapters/sinopac.py` | (Not yet created) — Must populate `source_version` and optionally `adapter_trace`. |
| `src/market_data_clean/adapters/finmind.py` | (Not yet created) — Must populate `source_version` and optionally `adapter_trace`. |
| `docs/api-sources/raw-input-contract.md` | No schema change needed (governance fields are added at pipeline, not in raw input). |

### 7.3 Proposed New Files

| File | Purpose |
|---|---|
| `governance.yaml` | (repo root) Default governance configuration template. Version-controlled. |
| `src/market_data_clean/governance.py` | Governance engine: config loader, validator, manifest builder, quality snapshot builder, audit log writer. |
| `src/market_data_clean/governance_schema.py` | Pydantic/dataclass models for governance entities (`RunManifest`, `QualitySnapshot`, `QualityConfig`, `AuditEntry`, `GovernanceConfig`, `OwnershipEntry`, `RetentionPolicy`). |
| `tests/test_governance.py` | Tests for governance config loading, validation, manifest generation, audit log append. |
| `tests/fixtures/governance_valid.yaml` | Test fixture: valid governance config for unit tests. |
| `tests/fixtures/governance_invalid_retention.yaml` | Test fixture: governance config with negative retention_days. |
| `tests/fixtures/governance_invalid_ownership.yaml` | Test fixture: governance config with missing required ownership fields. |

---

## 8. Out of Scope

The following are **explicitly excluded** from the first-pass governance foundation. Items are annotated with the DAMA DMBoK knowledge area(s) they relate to (see §2).

| Topic | DMBoK Area(s) | Rationale |
|---|---|---|
| **Data catalog / data dictionary service** | Metadata Management (9) | A searchable catalog is a downstream concern; this pass only defines metadata artifacts. |
| **Automated data archival / deletion** | Data Storage & Operations (3) | The governance layer produces advisories only. Actual file deletion or archival is left to operational tooling. |
| **RBAC / access control** | Data Security (4) | This repo is a library/CLI tool, not a service. Access control belongs in the deployment environment. |
| **PII / sensitive data detection** | Data Security (4) | Taiwan futures data does not contain personal information in scope. |
| **Full enterprise data architecture** | Data Architecture (1) | Pipeline architecture is documented but not formalised as an enterprise architecture framework. |
| **Schema evolution / migration tracking** | Data Modeling & Design (2) | The canonical schema is single-version for MVP. Schema versioning can be added later. |
| **Data warehousing / BI platform** | Data Warehousing & BI (8) | This is a data cleaning library. Downstream backtesting and research may warehouse independently. |
| **Real-time governance (streaming quality metrics)** | Data Quality Management (10) | The pipeline is batch-oriented. Streaming governance is a different architecture. |
| **Data masking / anonymisation** | Data Security (4) | Not applicable to futures OHLCV data. |
| **Cross-dataset join lineage** | Data Integration (5) | Lineage is per-row and per-run; cross-dataset relationships are out of scope. |
| **Cost tracking / storage optimisation** | Data Storage & Operations (3) | Retention advisory flags age but does not calculate storage costs. |
| **Integration with external governance tools (Apache Atlas, DataHub, Amundsen)** | Metadata Management (9) | The artifacts use plain JSON/YAML to stay tool-agnostic. Integration adapters can be built later. |

---

## 9. Suggested Implementation Phases

Each phase is annotated with the primary DAMA DMBoK knowledge areas it advances (see §2 for area definitions).

### Phase 1 — Core Engine (estimated: 2–3 days) [DMBoK-7, DMBoK-9, DMBoK-10]

1. Create `src/market_data_clean/governance_schema.py` with Pydantic/dataclass models for all governance entities (`GovernanceConfig`, `OwnershipEntry`, `RetentionPolicy`, `QualityConfig`, `RunManifest`, `QualitySnapshot`, `AuditEntry`).
2. Create `src/market_data_clean/governance.py` with:
   - `load_config(path) -> GovernanceConfig` — loads YAML/JSON, validates schema (DMBoK-7).
   - `build_manifest(run_id, config, input_stats, output_stats) -> RunManifest` (DMBoK-9).
   - `build_quality_snapshot(run_id, validation_results) -> QualitySnapshot`, respecting `quality.*` thresholds from config (DMBoK-10).
   - `append_audit_entry(audit_log_path, entry)` — appends to JSONL (DMBoK-9).
3. Add `pyyaml` to `pyproject.toml` dependencies.
4. Write `tests/test_governance.py` covering config loading, validation, manifest building.

### Phase 2 — CLI Integration (estimated: 1–2 days)

1. Add governance flags and subcommands to `cli.py` using Argparse subparsers.
2. Wire governance engine into the main pipeline: run manifest creation before data processing, quality snapshot after.
3. Add `--no-governance` bypass.
4. Implement `governance init-config` subcommand — writes the template with ownership, retention, quality, and adapters sections (DMBoK-7).
5. Implement `governance retention-check` subcommand (read-only scan, DMBoK-3).
6. Write integration tests for CLI flags.

### Phase 3 — Report Enrichment (estimated: 1 day) [DMBoK-7, DMBoK-9, DMBoK-10]

1. Enrich `report.json` with the `governance` key (ownership map, warnings, retention advisory).
2. Populate `governance.run_id` and `source_version` on each cleaned/rejected row (DMBoK-9).
3. Add `GovernanceConfig` copy to governance output directory.
4. Write tests verifying the enriched report structure.

### Phase 4 — Adapter Integration (estimated: 1 day) [DMBoK-5, DMBoK-9]

1. Update adapter stubs (or implementations when they are created) to populate `source_version` and `adapter_trace` (DMBoK-5: interoperability, DMBoK-9: lineage).
2. Update `raw-input-contract.md` if needed (unlikely — governance fields are pipeline-level).
3. Update `data-contract.md` with optional governance fields (DMBoK-2: data modeling).

### Phase 5 — Documentation & Template (estimated: 0.5 days) [DMBoK-6]

1. Commit `governance.yaml` template at repo root — includes all DMBoK-aligned sections (ownership, quality, retention, adapters).
2. Update `tasks.md` to reflect governance tasks.
3. Add governance section to `README.md`.

---

## 10. Future Skill Extraction Candidates

The following components from this governance work are good candidates for extraction into reusable skills (for use across other data pipeline projects):

| Candidate | DMBoK | Description | Extraction Trigger |
|---|---|---|---|
| **Governance Config Schema & Loader** | DMBoK-7, DMBoK-3 | Generic YAML/JSON config loader with Pydantic validation, ownership, retention, and quality models. Reusable for any data pipeline that needs stewardship metadata. | When a second project requires ownership tracking. |
| **Run Manifest Pattern** | DMBoK-9 | UUID-based run ID, input hash, adapter version tracking, git commit capture. Generic batch pipeline observability pattern. | When a second batch pipeline is created. |
| **Quality Snapshot Builder** | DMBoK-10 | Per-rule/per-source aggregation, null counts, z-score outlier detection. Reusable quality reporting engine. | When a second data quality project emerges. |
| **Audit Log (JSONL append)** | DMBoK-9 | Append-only JSONL pattern for immutable audit trails. | When audit logging is needed in another project. |
| **Retention Advisory Engine** | DMBoK-3 | Policy-driven file age scanner with category-based rules. | When file lifecycle management is needed across repos. |

Each of these could become a standalone Python module or a skill template that future projects import or adapt.
