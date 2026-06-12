# Data Governance MVP Implementation Checklist

## Phase 0 — Scout

- [ ] Confirm this is a batch data pipeline
- [ ] Check whether `governance.yaml` already exists
- [ ] Identify project/package name
- [ ] Identify data sources and adapter versions
- [ ] Identify pipeline entry points
- [ ] Identify output categories and existing contracts/docs
- [ ] Gather steward, owner, and domain defaults

## Phase 1 — Contract

- [ ] Create `docs/specs/data-governance/README.md`
- [ ] Use RFC 2119 language
- [ ] Add GIVEN/WHEN/THEN acceptance criteria
- [ ] Document ownership, retention, quality thresholds, and artifacts
- [ ] Map requirements to DMBoK MVP areas

## Phase 2 — Scaffold

- [ ] Create repo-root `governance.yaml`
- [ ] Ensure required retention categories are present
- [ ] Define ownership defaults
- [ ] Add at least one example override
- [ ] Define quality thresholds and outlier fields
- [ ] Define adapter/source version placeholders

## Phase 3 — Hook

- [ ] Load config near pipeline start
- [ ] Support explicit `run_id` or generate one
- [ ] Add `governance.run_id` to produced rows
- [ ] Add `source_version` to produced rows
- [ ] Emit manifest, quality snapshot, audit log, and config copy
- [ ] Support `--no-governance` bypass

## Phase 4 — Verify

- [ ] Valid config path passes
- [ ] Invalid config path fails clearly
- [ ] Audit log remains append-only
- [ ] Governance artifacts are created when enabled
- [ ] No governance artifacts are created when bypassed
- [ ] Retention-check path is read-only

## Phase 5 — Document

- [ ] Update `README.md`
- [ ] Update `docs/data-contract.md`
- [ ] Update `docs/validation-rules.md` if present
- [ ] Document runtime artifact meanings

## Review gates

- [ ] No overwrite of existing `governance.yaml`
- [ ] Retention remains advisory-only unless explicitly expanded
- [ ] Ownership/stewardship fields are explicit and reviewable
- [ ] Artifacts are plain JSON/YAML and repo-friendly
