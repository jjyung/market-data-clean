# Data Governance Skill — Extraction Specification

## 1. Feature Title & Context

**Feature:** `data-governance-skill`

**Context:**

This repository (`market-data-clean`) implements a concrete data governance foundation for a Taiwan futures data cleaning pipeline. The implementation spans `governance.yaml` (config), `src/market_data_clean/governance.py` (engine), `src/market_data_clean/governance_schema.py` (models), `tests/test_governance.py`, and CLI integration in `cli.py`. The original governance work is specified in `docs/specs/data-governance-foundation/README.md`.

This spec defines the extraction of that concrete implementation into a **reusable opencode skill** — a packaged workflow that any data pipeline project can invoke to stand up its own governance layer. The skill codifies the patterns, templates, and workflow discovered in the first implementation, but abstracts away the market-data-specific details (Taiwan futures, Sinopac/FinMind adapters, OHLCV schema).

The skill itself (once built) would live at `.opencode/skills/data-governance/SKILL.md` with supporting references, templates, and scripts. This spec is the **contract for building that skill**.

---

## 2. Skill Goal & Target Users

### Goal

Enable any data pipeline project to bootstrap a lightweight, DMBoK-aligned data governance layer with minimal effort. The skill guides a developer through:

1. Assessing the project's data landscape (sources, schemas, pipelines)
2. Scaffolding a governance configuration file (`governance.yaml`)
3. Generating governance-annotated data contracts
4. Installing governance hooks into the project's pipeline code
5. Producing governance artifacts (manifests, quality snapshots, audit logs) as sidecar outputs

### Target Users

| Role | How They Use the Skill |
|---|---|
| **Data Engineer** | Scaffolds governance config, wires CLI/API hooks into batch pipelines |
| **Platform Engineer** | Integrates governance into shared data pipeline tooling |
| **Data Scientist / Analyst** | Reads governance artifacts to assess data quality and lineage before research/backtesting |
| **Tech Lead / Architect** | Specifies ownership, retention, and quality policies via `governance.yaml` |
| **opencode Agent** | Invokes the skill via trigger phrases during development to ensure governance is considered from the start |

### Non-Goals

- The skill does **not** implement governance at runtime. It produces templates, config files, and code stubs that the project integrates.
- The skill does **not** enforce governance. It provides opt-in patterns.
- The skill does **not** manage deployed governance infrastructure (catalogs, RBAC, warehousing).

---

## 3. Trigger Phrases / When to Use

### Trigger Phrases (for opencode agent auto-detection)

```
data governance, governance, stewardship, data lineage, data quality,
retention policy, audit trail, run manifest, data contract, ownership,
DMBoK, metadata management, provenance tracking
```

### Explicit When-to-Use Guidance

Use this skill when:

- You are starting a **new data pipeline project** and want governance from day one
- An **existing pipeline** has no provenance tracking, no quality observability, and no ownership documentation
- A project needs to **pass a data governance audit** or meet internal compliance requirements
- You need to **document who owns each data source** and what retention policies apply
- You need **run-level traceability** (which pipeline version produced which output from which input)
- A code review reveals an **implicit governance decision** (e.g., "we keep raw data for 30 days") that should be codified

### When NOT to Use

- The project has no batch data pipeline (pure API service, frontend, mobile app)
- Governance is already handled by an enterprise platform (Apache Atlas, DataHub, Alation)
- The project needs real-time streaming governance (the skill targets batch pipelines)

---

## 4. Inputs the Skill Should Gather

Before generating artifacts, the skill must assess the target project. It gathers inputs via probing prompts or by reading project files.

### 4.1 Mandatory Inputs (must be collected or inferred)

| # | Input | Description | How to Gather |
|---|---|---|---|
| IN-01 | **Project name** | Human-readable project identifier | Prompt user or read `pyproject.toml`/`package.json`/`Cargo.toml` |
| IN-02 | **Data sources** | List of upstream data sources (APIs, files, databases) with names and versions | Prompt user or inspect `src/` for adapter patterns, `docker-compose.yml` for upstream services |
| IN-03 | **Pipeline entry points** | CLI commands, scripts, or functions that orchestrate data processing | Inspect for `main()`, `cli.py`, `__main__.py`, Makefile, Airflow DAGs |
| IN-04 | **Output categories** | Types of output the pipeline produces (e.g., `raw_input`, `cleaned`, `rejected`, `report`) | Inspect existing output directory patterns or prompt user |
| IN-05 | **Data domains** | Business domains the data belongs to (e.g., `futures`, `equities`, `fx`, `orders`) | Prompt user or read existing docs |
| IN-06 | **Existing data contracts** | Any existing schema definitions for inputs or outputs | Check for `docs/data-contract.md`, `docs/validation-rules.md`, OpenAPI specs, Avro/Protobuf schemas |

### 4.2 Optional Inputs (collected if available, else sensible defaults)

| # | Input | Default | Description |
|---|---|---|---|
| IN-07 | **Environment** | `development` | Deployment environment tag (`development`/`staging`/`production`) |
| IN-08 | **Data steward(s)** | Prompt user | Default email/team responsible for data |
| IN-09 | **Data owner(s)** | Prompt user | Default team name owning the data |
| IN-10 | **Retention defaults (days)** | raw: 30, cleaned: 365, rejected: 90, report: 730, manifest: 730 | How long to keep each output category |
| IN-11 | **Outlier fields** | `[]` (empty) | Which numeric fields to scan for z-score outliers |
| IN-12 | **Adapter versions** | `{}` (empty dict, inferred from IN-02) | Version strings for each data source adapter |
| IN-13 | **Programming language** | Auto-detect | Python (primary), but also support JS/TS, Go, Rust via templates |

### 4.3 Input Collection Strategy (Probes)

The skill should auto-detect what it can, then prompt for the rest:

```yaml
probe_sequence:
  - read pyproject.toml → # project name, python version, dependencies
  - read package.json →    # project name (JS/TS fallback)
  - read Cargo.toml →      # project name (Rust fallback)
  - glob src/**/cli.py →   # detect CLI entry points
  - glob src/**/adapters/ → # detect adapter patterns
  - glob governance.yaml →  # check if governance already exists (skip if so)
  - read docs/data-contract.md → # detect existing schema
  - prompt_for_remaining:  # ask user for anything not auto-detected
      - data_sources
      - data_steward
      - retention_days
```

---

## 5. Workflow / Phases

The skill guides the user through 6 phases. Each phase produces concrete outputs.

```
Phase 0: Scouting ──→ Read project, gather inputs
    │
    v
Phase 1: Contract ──→ Write docs/specs/data-governance/ (governance spec)
    │
    v
Phase 2: Scaffold ──→ Generate governance.yaml, schema stubs, config loader
    │
    v
Phase 3: Hook ──→ Add governance to pipeline entry points (CLI, functions)
    │
    v
Phase 4: Verify ──→ Run tests, validate artifacts
    │
    v
Phase 5: Document ──→ Update README, data contract, validation rules
```

### Phase 0 — Scouting (Est: 5-10 min)

**Goal:** Assess the target project and collect all inputs from §4.

**Steps:**

1. Read `pyproject.toml`, `package.json`, or equivalent to get project identity
2. Probe directory structure for pipeline entry points, adapters, and existing docs
3. Prompt user for remaining mandatory inputs (IN-01 through IN-06)
4. Determine programming language and existing patterns
5. Check for existing `governance.yaml` — if found, skip all phases and report existing setup
6. Write a `.handoffs/data-governance/scout-report.json` with collected inputs

**Outputs:**
- `.handoffs/data-governance/scout-report.json` (temporary, agent handoff)

### Phase 1 — Contract (Est: 15-30 min)

**Goal:** Write a project-specific governance spec that documents requirements, data ownership, retention, and quality thresholds — **before** generating any code.

**Steps:**

1. Create `docs/specs/data-governance/README.md` using inputs from Phase 0
2. Document each data source with ownership, steward, criticality
3. Define retention policies per output category
4. Define quality thresholds (outlier z-score, max rejection rate)
5. Reference DMBoK areas that each requirement serves
6. Present contract to user for approval

**Template for `docs/specs/data-governance/README.md`:**

```markdown
# Data Governance Specification — {{project_name}}

## Data Sources
| Source | Version | Domain | Steward | Owner | Criticality |
|--------|---------|--------|---------|-------|-------------|
| {{source_1}} | {{version}} | {{domain}} | {{steward}} | {{owner}} | {{criticality}} |

## Retention Policies
| Category | Retention Days | Archive After | Deletion After |
|----------|---------------|---------------|----------------|
| raw_input | {{days}} | {{days}} | {{days}} |

## Quality Thresholds
- Outlier z-score: {{z_score}}
- Max rejection rate: {{rate}}

## DMBoK Alignment
...

## Acceptance Criteria
GIVEN/W_HEN/THEN ...
```

**Outputs (persistent, committed):**
- `docs/specs/data-governance/README.md` — Governance specification

### Phase 2 — Scaffold (Est: 20-40 min)

**Goal:** Generate governance configuration file, data models, and a config loader/validator module in the project's language.

**Steps:**

1. Generate `governance.yaml` at repo root with ownership, retention, quality, and adapters sections (from gathered inputs)
2. Generate data model classes in the project's language:
   - **Python:** `src/<project>/governance_schema.py` — dataclasses/Pydantic models for `GovernanceConfig`, `OwnershipEntry`, `RetentionPolicy`, `QualityConfig`, `AdapterConfig`, `RunManifest`, `QualitySnapshot`, `AuditEntry`
   - **TypeScript:** `src/governance/schema.ts` — type definitions/interfaces
   - **Go:** `internal/governance/schema.go` — struct definitions
3. Generate config loader module:
   - **Python:** `src/<project>/governance.py` — `load_config()`, validation, `build_manifest()`, `build_quality_snapshot()`, `append_audit_entry()`, `source_version_for_row()`, `build_ownership_map()`, `collect_governance_warnings()`, `build_retention_advisory()`
   - (Other languages: analogous module with same public API surface)
4. Generate test fixtures:
   - `tests/fixtures/governance_valid.yaml`
   - `tests/fixtures/governance_invalid_retention.yaml`
5. Generate test file:
   - `tests/test_governance.py` — config loading, manifest building, audit append, init-config, retention-check
6. Add dependency (`PyYAML` for Python, `js-yaml` for JS/TS, `gopkg.in/yaml.v3` for Go) to project config

**Outputs (persistent, committed):**

| File | Language | Purpose |
|---|---|---|
| `governance.yaml` | YAML | Governance configuration (version-controlled) |
| `src/<project>/governance_schema.py` | Python | Data models for governance entities |
| `src/<project>/governance.py` | Python | Governance engine: loader, manifest builder, quality snapshot, audit, retention |
| `tests/fixtures/governance_valid.yaml` | YAML | Valid config for tests |
| `tests/fixtures/governance_invalid_retention.yaml` | YAML | Invalid config for error-path tests |
| `tests/test_governance.py` | Python | Unit tests for governance module |

### Phase 3 — Hook (Est: 15-30 min)

**Goal:** Wire governance into the project's pipeline entry points so that governance artifacts are produced automatically during runs.

**Steps:**

1. **Locate pipeline entry point(s):**
   - CLI (`cli.py` / `main.py`): Add `--governance-config`, `--run-id`, `--governance-output`, `--no-governance` flags, `governance init-config` and `governance retention-check` subcommands
   - Function API: Add `GovernanceOptions` parameter to pipeline functions
   - Makefile / scripts: Add governance check targets
2. **Inject governance at pipeline boundaries:**
   - Before processing: load config, generate `run_id`, capture input stats (row count, sha256)
   - After validation but before writing outputs: attach `governance.run_id`, `source_version`, `adapter_trace`, `quality_score` to each row
   - After writing outputs: build manifest, quality snapshot, audit entry, retention advisory; enhance report
3. **Wire governance data flow:**

```
Pipeline Start
  │
  ├── load governance config (or skip if --no-governance)
  ├── generate run_id
  │
  ▼
Read Input ──→ Validate ──→ Enrich Rows ──→ Write Outputs
                  │            │
                  │            ├── add governance.run_id
                  │            ├── add source_version
                  │            ├── add adapter_trace
                  │            └── add quality_score
                  │
                  ▼
          Build Governance Artifacts
                  │
                  ├── manifest.json (run_id, timestamps, input stats, adapter versions)
                  ├── quality.json (per-rule/per-source breakdown, null counts, outliers)
                  ├── audit_log.jsonl (append-only entry)
                  └── config_used.yaml (copy of config at run time)
                  │
                  ▼
          Enrich Report
                  │
                  └── add governance key (ownership_map, warnings, retention_advisory)
                  │
                  ▼
Pipeline End
```

4. **Add the `governance init-config` subcommand** — writes a default `governance.yaml` template
5. **Add the `governance retention-check` subcommand** — scans data directory against retention policies (read-only)

**Outputs (persistent, committed):**

| File Change | Description |
|---|---|
| `src/<project>/cli.py` or equivalent | Governance flags and subcommands added |
| Pipeline function signature | `GovernanceOptions` parameter added (if function API) |

### Phase 4 — Verify (Est: 10-15 min)

**Goal:** Run generated tests and validate end-to-end governance artifacts.

**Steps:**

1. Run `pytest tests/test_governance.py -v` (or equivalent test command)
2. Verify all acceptance criteria from §8 pass
3. Run a sample pipeline end-to-end with governance enabled
4. Inspect governance artifacts:
   - `_governance/manifest.json` — correct structure
   - `_governance/quality.json` — per-rule breakdown matches expectations
   - `_governance/audit_log.jsonl` — append-only, correct format
   - `report.json` — contains `governance` key with ownership, warnings, retention
   - Output rows — contain `governance.run_id`, `source_version`
5. Run with `--no-governance` — confirm no governance artifacts produced
6. Run with invalid config — confirm graceful error with clear message

**Outputs:**
- `.handoffs/data-governance/verify-report.json` (temporary)

### Phase 5 — Document (Est: 10-15 min)

**Goal:** Update project documentation to reflect governance capabilities.

**Steps:**

1. Update `docs/data-contract.md` — add governance metadata fields (`governance.run_id`, `source_version`, `adapter_trace`, `quality_score`)
2. Update `docs/validation-rules.md` — add governance config validation rules
3. Update `README.md` — add governance section: how to configure, how to use CLI flags, how to read artifacts
4. (Optional) Create a governance-usage example in `docs/governance-quickstart.md`

**Outputs (persistent, committed):**
- Updated `docs/data-contract.md`
- Updated `docs/validation-rules.md` (if exists)
- Updated `README.md`

---

## 6. Required Outputs / Artifacts

### 6.1 Persistent Artifacts (committed to repo)

| Artifact | Location | Phase | Description |
|---|---|---|---|
| Governance spec | `docs/specs/data-governance/README.md` | Phase 1 | Project-specific governance requirements and design |
| Governance config | `governance.yaml` | Phase 2 | Ownership, retention, quality, adapters configuration |
| Governance schema | `src/<project>/governance_schema.py` | Phase 2 | Data models for governance entities |
| Governance engine | `src/<project>/governance.py` | Phase 2 | Config loader, manifest builder, quality snapshot builder, audit logger, retention scanner |
| Test fixtures | `tests/fixtures/governance_valid.yaml` | Phase 2 | Valid governance config for testing |
| Test fixtures | `tests/fixtures/governance_invalid_retention.yaml` | Phase 2 | Invalid governance config for error-path testing |
| Tests | `tests/test_governance.py` | Phase 2 | Unit and integration tests for governance |
| Modified CLI | `src/<project>/cli.py` (modified) | Phase 3 | Governance flags and subcommands added |
| Updated data contract | `docs/data-contract.md` (modified) | Phase 5 | Governance metadata fields documented |
| Updated README | `README.md` (modified) | Phase 5 | Governance usage instructions |

### 6.2 Runtime Artifacts (produced during pipeline runs)

| Artifact | File | Format | Description |
|---|---|---|---|
| Run Manifest | `_governance/manifest.json` | JSON | Single immutable object per run |
| Quality Snapshot | `_governance/quality.json` | JSON | Single immutable object per run |
| Audit Log | `_governance/audit_log.jsonl` | JSON Lines | Append-only, one entry per run |
| Config Copy | `_governance/config_used.yaml` | YAML/JSON | Snapshot of config at run time |
| Report Enrichment | `report.json` (governance key) | JSON | Runtime ownership map, warnings, retention advisory |

### 6.3 Temporary Artifacts (handoffs, never committed)

| Artifact | Location | Phase | Description |
|---|---|---|---|
| Scout report | `.handoffs/data-governance/scout-report.json` | Phase 0 | Collected project inputs |
| Verify report | `.handoffs/data-governance/verify-report.json` | Phase 4 | Test results and artifact validation |

---

## 7. DMBoK Area Mapping — MVP Focus vs Optional

### 7.1 Skill Coverage by DMBoK Area

| # | Knowledge Area | Skill Coverage | Phase | Notes |
|---|---|---|---|---|
| 1 | **Data Architecture** | 🔶 **Light** | Phase 0 | Skill catalogs existing pipeline architecture but does not design it |
| 2 | **Data Modeling & Design** | 🎯 **MVP Focus** | Phase 2, 5 | Generates governance schema models and annotates data contracts with governance metadata fields |
| 3 | **Data Storage & Operations** | 🎯 **MVP Focus** | Phase 2, 3 | Scaffolds retention policies and retention-check subcommand (advisory-only, no auto-delete) |
| 4 | **Data Security** | ⏭️ **Out of Scope** | — | RBAC, encryption, access control are deployment-level concerns; the skill adds a `classification` field for future tagging |
| 5 | **Data Integration & Interoperability** | 🎯 **MVP Focus** | Phase 2, 3 | Adapter version tracking (`source_version`, `adapter_trace`) preserves source provenance across integration boundaries |
| 6 | **Document & Content Management** | 🎯 **MVP Focus** | Phase 1, 5 | Generates governance spec and updates project docs (data contract, README) |
| 7 | **Reference & Master Data** | 🎯 **MVP Focus** | Phase 2 | `governance.yaml` ownership section serves as lightweight symbol/source reference data registry |
| 8 | **Data Warehousing & BI** | ⏭️ **Out of Scope** | — | The skill targets data pipeline governance, not warehousing |
| 9 | **Metadata Management** | 🎯 **MVP Focus** | Phase 2, 3, 4 | Manifests, audit logs, adapter version tracking, config snapshots — all operational metadata |
| 10 | **Data Quality Management** | 🎯 **MVP Focus** | Phase 2, 3 | Quality snapshots (per-rule, per-source, null counts, z-score outliers), configurable thresholds |

### 7.2 Coverage Summary

| Classification | Areas | Count |
|---|---|---|
| 🎯 MVP Focus | Data Modeling & Design, Data Storage & Operations, Data Integration & Interoperability, Document & Content Management, Reference & Master Data, Metadata Management, Data Quality Management | **7** |
| 🔶 Lightly Addressed | Data Architecture | **1** |
| ⏭️ Out of Scope | Data Security, Data Warehousing & BI | **2** |

### 7.3 Implementation Priority (for skill builder)

| Priority | DMBoK Areas | Rationale |
|---|---|---|
| **P0 — Ship** | 2, 5, 6, 7, 9, 10 | Core governance value: config, lineage, quality, ownership, docs |
| **P1 — Ship** | 3 | Retention is important but advisory-only; can be a follow-up |
| **P2 — Future** | 1, 4, 8 | Enterprise architecture, security, BI integration — depends on platform needs |

---

## 8. Acceptance Criteria for the Skill Itself

These ACs govern the data-governance skill as a product. They are GIVEN/WHEN/THEN criteria that the skill author must satisfy.

### AC-SKILL-01: Skill is triggered by governance keywords

```
GIVEN a user types "data governance" or "governance" or "stewardship" in an opencode conversation
 WHEN the skill is available
 THEN the skill auto-activates and begins Phase 0 (Scouting)
```

### AC-SKILL-02: Skill detects existing governance and skips

```
GIVEN a project that already has a `governance.yaml` at the repo root
 WHEN the skill runs Phase 0
 THEN the skill reports "Governance already configured at governance.yaml"
  AND it does not overwrite or modify the existing file
  AND it exits Phase 0 without proceeding to Phase 1
```

### AC-SKILL-03: Skill produces a governance spec

```
GIVEN a project with no existing governance
 WHEN the skill completes Phase 1
 THEN `docs/specs/data-governance/README.md` exists
  AND it documents data sources, ownership, retention policies, quality thresholds
  AND it uses RFC 2119 language (MUST/SHOULD/MAY)
  AND it includes GIVEN/WHEN/THEN acceptance criteria
```

### AC-SKILL-04: Skill scaffolds working governance.yaml

```
GIVEN Phase 2 completes
 WHEN the user runs `governance init-config`
 THEN a `governance.yaml` with `version`, `metadata`, `ownership`, `retention`,
      `quality`, and `adapters` sections is written
  AND it passes the built-in config validator
  AND all required retention categories (raw_input, cleaned, rejected, report, manifest) are present
```

### AC-SKILL-05: Skill generates testable governance code

```
GIVEN Phase 2 completes for a Python project
 WHEN the user runs `pytest tests/test_governance.py -v`
 THEN all tests pass
  AND tests cover: valid config loading, invalid config rejection, audit log append,
      init-config command, retention-check command, end-to-end pipeline with governance artifacts
```

### AC-SKILL-06: Skill wires governance into pipeline entry points

```
GIVEN Phase 3 completes
 WHEN the pipeline runs with governance enabled
 THEN `_governance/manifest.json`, `_governance/quality.json`, `_governance/audit_log.jsonl`,
      and `_governance/config_used.yaml` are all produced
  AND each output row contains `governance.run_id` and `source_version` fields
```

### AC-SKILL-07: Skill supports --no-governance bypass

```
GIVEN a pipeline with governance wired in
 WHEN the user passes `--no-governance`
 THEN no governance artifacts are produced
  AND the pipeline produces only core outputs (cleaned.csv, rejected.csv, report.json)
```

### AC-SKILL-08: Skill gracefully handles invalid config

```
GIVEN a governance config with a negative retention_days value
 WHEN the pipeline starts
 THEN the pipeline aborts before processing data
  AND a clear error message identifies the invalid field and value
```

### AC-SKILL-09: Skill generates language-appropriate artifacts

```
GIVEN Phase 2 is run for a Python project
 WHEN the generated code is inspected
 THEN `governance_schema.py` uses @dataclass and type hints
  AND `governance.py` has a `load_config()` function
  AND `test_governance.py` uses pytest

GIVEN Phase 2 is run for a TypeScript project
 WHEN the generated code is inspected
 THEN `governance/schema.ts` uses TypeScript interfaces
  AND a corresponding governance module is generated
```

### AC-SKILL-10: Skill produces DMBoK-aligned artifacts

```
GIVEN the skill completes all phases
 WHEN artifacts are audited against DMBoK areas
 THEN:
   - Ownership & stewardship artifacts exist (DMBoK-7)
   - Retention policies are defined (DMBoK-3)
   - Lineage metadata (run_id, source_version) is tracked (DMBoK-9)
   - Quality snapshots are emitted (DMBoK-10)
   - Data contract is updated with governance fields (DMBoK-2)
   - Adapter versions are trackable (DMBoK-5)
```

---

## 9. Proposed Files for Skill Implementation

### 9.1 Skill Root

```
.opencode/skills/data-governance/
├── SKILL.md                    # Main skill definition (see §9.2 for structure)
├── references/
│   ├── governance.yaml         # Template governance config (extracted from market-data-clean)
│   ├── governance-spec.md      # Template for docs/specs/data-governance/README.md
│   ├── data-contract-fragment.md  # Governance metadata fields to add to existing data contract
│   └── dmbok-mapping.md        # DMBoK area descriptions and alignment guide
├── scripts/
│   ├── scaffold-config.py      # Python script that generates governance.yaml from inputs
│   ├── scaffold-python.py      # Generates governance_schema.py + governance.py + test files
│   ├── scaffold-typescript.ts  # Generates TypeScript governance module
│   ├── scaffold-go.go          # Generates Go governance module
│   └── hook-cli.py             # Injects governance flags into existing cli.py
└── templates/
    ├── governance.py.j2         # Jinja2 template for Python governance engine
    ├── governance_schema.py.j2  # Jinja2 template for Python data models
    ├── test_governance.py.j2    # Jinja2 template for Python tests
    ├── governance_schema.ts.j2  # Jinja2 template for TypeScript types
    ├── governance.go.j2         # Jinja2 template for Go structs
    ├── manifest.json.j2         # Template for manifest runtime artifact
    └── quality.json.j2          # Template for quality snapshot runtime artifact
```

### 9.2 SKILL.md Structure

Following the existing skill convention (see `.opencode/skills/adr/SKILL.md`, `dev-flow/SKILL.md`):

```markdown
---
name: data-governance
description: |
  Bootstrap a lightweight DMBoK-aligned data governance layer for any batch data pipeline.
  Scaffolds governance configuration, data models, pipeline hooks, and documentation.
  Triggers on: "data governance", "governance", "stewardship", "lineage",
  "data quality", "retention policy", "audit trail", "run manifest",
  "data contract", "ownership", "DMBoK", "metadata management"
---

# Data Governance Skill

<Goal and target users from §2>

## When to Use

<Trigger guidance from §3>

## Workflow Overview

Phase 0: Scouting → Phase 1: Contract → Phase 2: Scaffold → Phase 3: Hook → Phase 4: Verify → Phase 5: Document

### Phase 0: Scouting
...
### Phase 1: Contract
...
### Phase 2: Scaffold
...
### Phase 3: Hook
...
### Phase 4: Verify
...
### Phase 5: Document
...

## Inputs Required

| Input | Required | Auto-detectable | Prompt |
|---|---|---|---|
| Project name | Yes | Yes (pyproject.toml) | Fallback |
| Data sources | Yes | Partial (adapter dirs) | Yes |
| ... | ... | ... | ... |

## Outputs Produced

| Phase | Output | Location | Persistent |
|---|---|---|---|
| 1 | Governance spec | docs/specs/data-governance/ | ✅ |
| 2 | Config, schema, engine, tests | Various | ✅ |
| 3 | CLI hooks | src/<project>/cli.py | ✅ |
| 4 | Verify report | .handoffs/ | ❌ |
| 5 | Updated docs | docs/, README.md | ✅ |

## DMBoK Alignment

...
```

### 9.3 Migration Plan for Template Files

The following files from `market-data-clean` will be extracted into the skill's `references/` and `templates/` directories:

| Source (market-data-clean) | Destination (skill) | Transformation |
|---|---|---|
| `governance.yaml` | `references/governance.yaml` | Replace market-specific values (sinopac, finmind, TX/MTX symbols) with `{{placeholder}}` markers |
| `src/market_data_clean/governance_schema.py` | `templates/governance_schema.py.j2` | Parameterize project name, add type annotations as variables; extract as Jinja2 template |
| `src/market_data_clean/governance.py` | `templates/governance.py.j2` | Same: replace `market_data_clean` with `{{package_name}}`; keep all core logic (config loading, manifest building, quality snapshots, audit, retention) |
| `src/market_data_clean/cli.py` (governance sections) | `templates/cli-governance-fragment.py.j2` | Extract only the governance-related CLI code (parser additions, subcommands, pipeline wiring) |
| `tests/test_governance.py` | `templates/test_governance.py.j2` | Parameterize package name and fixture paths |
| `tests/fixtures/governance_valid.yaml` | `templates/test-fixture-valid.yaml.j2` | Replace project-specific symbols with generic placeholders |
| `tests/fixtures/governance_invalid_retention.yaml` | `templates/test-fixture-invalid-retention.yaml.j2` | Same |
| `docs/specs/data-governance-foundation/README.md` | `references/governance-spec.md` | Extract the DMBoK mapping, AC templates, and artifact contract as reusable spec patterns |
| `docs/data-contract.md` (governance fields) | `references/data-contract-fragment.md` | Extract just the governance metadata fields section as an insert fragment |

---

## 10. Migration / Extraction Notes

### 10.1 Concrete-to-Abstract Mapping

The following table maps each concrete component in `market-data-clean` to the abstract pattern the skill should generate:

| Concrete (market-data-clean) | Abstract (skill pattern) | Generalization Strategy |
|---|---|---|
| `market_data_clean` package | `{{package_name}}` | Parameterize via templates; detect from project config |
| Sinopac + FinMind adapters | `{{source_list}}` | Prompt user for sources; generate `adapters:` section from inputs |
| TX / MTX symbols | `{{symbol_list}}` or `{{source_list}}` | Ownership entries are per-source, not per-symbol; let user define overrides |
| OHLCV schema | User-defined schema | Skill does not assume a fixed schema; governance fields are added to whatever schema exists |
| `docs/data-contract.md` | User's existing data contract | Skill appends governance metadata fields; does not overwrite existing contracts |
| `market-data-clean` CLI name | `{{cli_name}}` read from `project.scripts` in pyproject.toml | Auto-detect CLI entry point |
| Python-specific | Python + TS + Go templates | Write templated versions for each target language |
| `_governance/` output dir | `{{governance_output_dir}}` | Configurable, default `_governance/` |
| Taiwan futures domain | User-defined domain | Prompt for `data_domain` during scouting |
| `shioaji` library dependency | `PyYAML` only required | Governance module has minimal dependencies; market-specific deps are user's concern |

### 10.2 What Stays the Same (No Abstraction Needed)

These components are already generic and can be directly templated:

- **Config schema** (`governance.yaml` structure): `version`, `metadata`, `ownership` (defaults + overrides), `retention` (policies), `quality` (thresholds), `adapters` — already domain-agnostic
- **Config validation logic**: ownership required fields, retention category checks, quality value ranges — reusable as-is
- **Run manifest structure**: `run_id`, `cli_version`, `git_commit_hash`, `input`, `adapter_versions`, `output` — generic batch pipeline pattern
- **Quality snapshot structure**: `summary`, `per_rule_breakdown`, `per_source_breakdown`, `field_null_counts`, `outlier_flags` — generic
- **Audit log format**: JSON Lines append — generic pattern
- **Retention advisory logic**: policy-driven file age scanner — generic
- **CLI flags**: `--governance-config`, `--run-id`, `--governance-output`, `--no-governance` — generic

### 10.3 What Must Be Generalized

| Component | Current (Concrete) | Needed (Abstract) |
|---|---|---|
| Validation rules | Market-specific (negative_price, high_lt_max_open_close) | Configurable or user-defined; skill generates placeholder rule list |
| Outlier fields | `volume`, `close` | Read from `quality.outlier_fields` in config; user-defined |
| Data source detection | Assumes Sinopac/FinMind adapters | Probe `src/**/adapters/` or prompt user |
| CLI integration | Argparse-specific | Python: argparse/click/typer; TS: commander/yargs |
| Language support | Python only | Multi-language templates (Python P0, TS/JS P1, Go P2) |

### 10.4 Extraction Procedure

To build the skill from the existing implementation:

```
Step 1: Extract reference files
  cp governance.yaml .opencode/skills/data-governance/references/governance.yaml
  # Replace concrete values with {{placeholder}} markers

Step 2: Create Jinja2 templates from source code
  cp src/market_data_clean/governance_schema.py templates/governance_schema.py.j2
  cp src/market_data_clean/governance.py templates/governance.py.j2
  cp tests/test_governance.py templates/test_governance.py.j2
  cp tests/fixtures/governance_valid.yaml templates/test-fixture-valid.yaml.j2
  cp tests/fixtures/governance_invalid_retention.yaml templates/test-fixture-invalid-retention.yaml.j2
  # Replace market_data_clean → {{package_name}} in all templates
  # Replace market-data-clean → {{project_name}} in all templates
  # Replace concrete adapter examples with {{source_list}} loops

Step 3: Write scaffold scripts
  scripts/scaffold-config.py    # Reads inputs, renders governance.yaml template
  scripts/scaffold-python.py    # Reads inputs, renders Python templates
  scripts/hook-cli.py           # Reads inputs, modifies CLI entry point

Step 4: Write SKILL.md
  # Follow the structure from §9.2, referencing scripts and templates

Step 5: Write reference docs
  references/governance-spec.md       # Template for docs/specs/data-governance/README.md
  references/data-contract-fragment.md  # Governance fields to append to data contracts
  references/dmbok-mapping.md         # DMBoK area primer for users

Step 6: Test the skill
  # Create a test project, invoke the skill, verify all artifacts are correct
  # Run generated tests, verify acceptance criteria
```

### 10.5 Integration with Existing Skills

The data-governance skill should reference and be referenced by:

| Skill | Relationship |
|---|---|
| `dev-flow` | Governance spec (`docs/specs/data-governance/`) follows dev-flow contract format; phases 1 and 5 align |
| `adr` | A new project may write an ADR before adopting governance (e.g., ADR: "Use DMBoK data governance framework") |
| `test-gen` | Governance tests (`tests/test_governance.py`) can be generated or extended by test-gen |
| `docs-gen` | Governance documentation updates (data contract, README) align with docs-gen conventions |
| `orchestrate` | For complex multi-repo governance rollouts, orchestrate can dispatch the skill across repos |

---

## 11. Out of Scope

The following are **explicitly excluded** from the data-governance skill spec. Items are annotated with the DMBoK knowledge areas they relate to.

| Topic | DMBoK Area(s) | Rationale |
|---|---|---|
| Real-time / streaming governance | Data Quality Management (10) | The skill targets batch pipelines; streaming governance requires different architecture (windowed quality metrics, event-time lineage) |
| Data catalog / searchable metadata | Metadata Management (9) | A catalog is a platform concern; the skill produces metadata artifacts that a catalog could ingest |
| Automated data archival / deletion | Data Storage & Operations (3) | The skill generates retention policies and a read-only check command; actual file operations are left to ops tooling |
| RBAC / access control | Data Security (4) | Deployment-level concern; the skill adds a `classification` field but does not enforce access |
| Enterprise data architecture | Data Architecture (1) | The skill catalogs existing architecture but does not design or restructure it |
| Schema evolution / migration tracking | Data Modeling & Design (2) | Governance metadata fields are additive; schema versioning is out of scope |
| Data warehousing / BI | Data Warehousing & BI (8) | The skill targets pipeline governance, not warehousing |
| Cross-dataset join lineage | Data Integration (5) | Lineage is per-run and per-row; cross-dataset lineage is a future enhancement |
| Cost tracking / storage optimisation | Data Storage & Operations (3) | Retention advisory flags age but does not calculate costs |
| Integration with external tools (Atlas, DataHub, Amundsen) | Metadata Management (9) | Artifacts use plain JSON/YAML to stay tool-agnostic; integration adapters can be built later |
| Data masking / anonymisation | Data Security (4) | Not applicable to non-PII batch data pipelines |
| PII / sensitive data detection | Data Security (4) | The skill does not inspect data content for sensitive fields |
| Modification of existing governance | — | If `governance.yaml` exists, the skill skips all phases — it never overwrites |

---

## 12. Architecture References

This spec does not introduce new architectural decisions but extracts/concretises patterns from this repo's existing governance work. Key reference points:

| Reference | Relation |
|---|---|
| `docs/specs/data-governance-foundation/README.md` | Source spec for the original governance implementation; this skill spec is a direct extraction from it |
| `governance.yaml` | Concrete governance config that the skill generalises into a template |
| `src/market_data_clean/governance.py` | Concrete governance engine that becomes the skill's Python template |
| `src/market_data_clean/governance_schema.py` | Concrete data models that become the skill's schema template |
| `src/market_data_clean/cli.py` | Concrete CLI integration that the skill's hook phase emulates |
| `tests/test_governance.py` | Concrete test suite that becomes the skill's test template |
| `.opencode/skills/adr/SKILL.md` | Existing skill format precedent (frontmatter, phases, trigger phrases, related skills) |
| `.opencode/skills/dev-flow/SKILL.md` | Existing skill format precedent (phase overview, step details, artifact summaries) |

No new ADRs are needed for this extraction — the governance pattern is already proven in this repo. A future project adopting the skill may write an ADR documenting their decision to use this governance framework.

---

## 13. Implementation Phases (for building the skill)

### Phase A — Template Extraction (Est: 1-2 days)

1. Create directory structure under `.opencode/skills/data-governance/`
2. Extract `governance.yaml` → `references/governance.yaml` with `{{placeholder}}` markers
3. Create Jinja2 templates from `governance_schema.py`, `governance.py`, `test_governance.py`, test fixtures
4. Parameterize package name, project name, CLI name, source list, retention defaults
5. Write `scripts/scaffold-config.py` — renders governance.yaml from inputs

### Phase B — Code Generation Scripts (Est: 2-3 days)

1. Write `scripts/scaffold-python.py` — renders Python governance module, schema, tests
2. Write `scripts/hook-cli.py` — injects governance flags into existing cli.py (Argparse only for MVP; click/typer P1)
3. Write `scripts/scaffold-typescript.ts` — renders TypeScript governance types (P1)
4. Test all scripts against a clean project scaffold

### Phase C — SKILL.md Write (Est: 0.5 day)

1. Write `.opencode/skills/data-governance/SKILL.md` following the structure from §9.2
2. Write `references/governance-spec.md` — template for Phase 1 output
3. Write `references/data-contract-fragment.md` — governance metadata fields
4. Write `references/dmbok-mapping.md` — DMBoK primer for users

### Phase D — Validation (Est: 0.5 day)

1. Create a test project: `mkdir /tmp/test-gov && cd /tmp/test-gov && python -m venv .venv && pip install pytest pyyaml`
2. Run the skill against the test project
3. Verify all Phase 1-5 outputs are correct
4. Run generated tests, verify all pass
5. Fix any issues

---

## Files Created (This Spec)

| File | Purpose |
|---|---|
| `docs/specs/data-governance-skill/README.md` | This document — persistent contract for building the data governance skill |
