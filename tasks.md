# Governance-First Backlog: market-data-clean

This file tracks the implementation backlog for `market-data-clean` with **data governance built in from the start**. Edit checkboxes as work completes (`[ ]` -> `[x]`).

---

## Phase 0: Environment & Baseline

- [x] Create Python virtual environment (`python -m venv .venv`).
- [x] Install dependencies in development/editable mode (`uv pip install -e .` or `pip install -e .`).
- [x] Install test dependencies (`pytest`).
- [x] Run `pytest` to verify the initial scaffold passes.
- [x] Add governance dependency support (`PyYAML`) for governance config loading.

```bash
uv add pytest shioaji
uv run pytest
```

---

## Phase 1: Source Survey & Data Architecture

### 1.1 Source documentation

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

### 1.2 Unified contracts and data layers

- [x] Define unified raw input contract → `docs/api-sources/raw-input-contract.md`
  - [x] OHLCV Pipeline (主) — 支援期貨日資料與即時報價
  - [x] OrderBook Pipeline (輔) — 五檔報價獨立處理
  - [x] API-to-unified mapping table for both sources
  - [x] Timezone normalization rules
- [ ] Document the repo data-layer model explicitly:
  - [ ] `raw_input` layer
  - [ ] `cleaned` layer
  - [ ] `rejected` / exception layer
  - [ ] `reference/master metadata` layer
- [ ] Clarify scope boundaries for **加權指數期貨 / 小台指期貨** only.

---

## Phase 2: Governance Foundation

### 2.1 Governance contracts and docs

- [x] Create governance foundation spec → `docs/specs/data-governance-foundation/README.md`
- [x] Align governance scope with DAMA DMBoK knowledge areas.
- [x] Create governance skill extraction spec → `docs/specs/data-governance-skill/README.md`

### 2.2 Governance configuration

- [x] Add repo-root governance config → `governance.yaml`
- [x] Define ownership / stewardship defaults and overrides.
- [x] Define retention policies for:
  - [x] `raw_input`
  - [x] `cleaned`
  - [x] `rejected`
  - [x] `report`
  - [x] `manifest`
- [x] Define quality thresholds:
  - [x] `outlier_z_score`
  - [x] `max_rejection_rate`
  - [x] `outlier_fields`
- [x] Define adapter-version metadata placeholders.

### 2.3 Governance metadata and auditability

- [x] Extend canonical data contract with governance metadata fields.
  - [x] `governance.run_id`
  - [x] `source_version`
  - [x] `adapter_trace`
  - [x] `quality_score`
- [x] Define manifest / quality snapshot / audit log artifacts.
- [x] Define governance config validation rules.

---

## Phase 3: Example Data & Reference Data

- [ ] Create `examples/raw_data.csv` in unified format.
  - [ ] Include rows from multiple sources (`source` column)
  - [ ] Include intentionally malformed rows
  - [ ] Include intentionally duplicated rows
- [ ] Add a lightweight reference/master-data example for symbols and source ownership.
- [ ] Document symbol/source ownership completeness expectations.

---

## Phase 4: Pipeline Core Implementation

### 4.1 Source adapters

- [ ] Create `src/market_data_clean/adapters/`.
- [ ] Implement `sinopac.py` adapter for **期貨即時成交 / quote** → unified OHLCV format.
  - [ ] Support `TickFOPv1` / `QuoteFOPv1` normalization.
  - [ ] Normalize `date + time` into UTC `timestamp`.
  - [ ] Map `Decimal` fields into Python numeric types.
  - [ ] Populate source provenance fields needed by governance.
- [ ] Implement `finmind.py` adapter for **期貨日資料 / snapshot** → unified OHLCV format.
  - [ ] Support `TaiwanFuturesDaily` normalization.
  - [ ] Support `taiwan_futures_snapshot` normalization.
  - [ ] Populate source provenance fields needed by governance.
- [ ] Defer `BidAskFOPv1` / order book pipeline to a later phase.

### 4.2 Parser

- [ ] Create `src/market_data_clean/parser.py`.
- [ ] Implement parser entrypoints for:
  - [ ] unified CSV input
  - [ ] list of dicts / DataFrame input from adapters
- [ ] Ensure datetimes are parsed as timezone-aware UTC.
- [ ] Validate required unified fields are present before entering validator.

### 4.3 Validator

- [ ] Create `src/market_data_clean/validator.py`.
- [ ] Implement row-level validation for **OHLCV pipeline**:
  - [ ] no negative prices / volume
  - [ ] `high >= max(open, close)`
  - [ ] `low <= min(open, close)`
- [ ] Implement dataset-level validation:
  - [ ] detect duplicate `(symbol, timestamp)` rows
  - [ ] report missing required fields
- [ ] Separate rows into `cleaned` and `rejected` with specific reasons.
- [ ] Keep order book validation out of MVP for now.

---

## Phase 5: CLI & Governance Runtime Hooks

### 5.1 Core CLI

- [x] Update `src/market_data_clean/cli.py` to accept input path and output directory.
- [ ] Run parser and validator modules through the CLI once they exist.
- [x] Write `cleaned.csv`, `rejected.csv`, and `report.json`.

### 5.2 Governance-aware CLI

- [x] Add governance flags:
  - [x] `--governance-config`
  - [x] `--run-id`
  - [x] `--governance-output`
  - [x] `--no-governance`
- [x] Add subcommands:
  - [x] `governance init-config`
  - [x] `governance retention-check`
- [x] Emit governance artifacts:
  - [x] `manifest.json`
  - [x] `quality.json`
  - [x] `audit_log.jsonl`
  - [x] `config_used.yaml`
- [x] Enrich report output with governance sections.

---

## Phase 6: Testing & Verification

### 6.1 Data pipeline tests

- [ ] Create tests verifying:
  - [ ] valid unified OHLCV rows are preserved
  - [ ] invalid rows are rejected with expected reasons
  - [ ] duplicate `(symbol, timestamp)` rows are handled properly
  - [ ] adapter outputs match the unified contract

### 6.2 Governance tests

- [x] Create governance tests under `tests/` verifying:
  - [x] valid governance config loads
  - [x] invalid governance config is rejected
  - [x] audit log append behavior
  - [x] `init-config` command
  - [x] `retention-check` command
  - [x] main CLI writes governance artifacts when enabled
- [ ] Add tests for `--no-governance` bypass behavior.
- [ ] Add tests for ownership completeness warnings across multiple symbols/sources.

### 6.3 End-to-end verification

- [ ] Run the pipeline against `examples/raw_data.csv`.
- [ ] Verify `cleaned.csv`, `rejected.csv`, and `report.json` are written correctly.
- [ ] Verify governance artifacts are written correctly under `_governance/`.
- [ ] Verify sample data remains inside **TX / MTX** scope.

---

## Phase 7: Reuse & Tooling

- [x] Extract reusable opencode governance skill → `.opencode/skills/data-governance/`
- [x] Add templates for:
  - [x] governance spec
  - [x] governance config
  - [x] implementation checklist
  - [x] data contract fragment
  - [x] DMBoK mapping reference
- [ ] Validate the skill against a second repo / workspace.
- [ ] Consider adding scaffold scripts once reuse patterns stabilize.
