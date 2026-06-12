# Data Governance Skill References

Use these files as the reusable MVP toolkit for governance rollout.

## Reference files

| File | Purpose |
|---|---|
| `data-contract-fragment.md` | Ready-to-copy governance fields for an existing data contract |
| `dmbok-mapping.md` | DMBoK MVP coverage guide for lightweight pipeline governance |

## Template files

| File | Purpose |
|---|---|
| `../templates/governance.yaml` | Seed config with ownership, retention, quality, and adapters |
| `../templates/governance-spec.md` | Contract-first governance spec template |
| `../templates/implementation-checklist.md` | Practical rollout and review checklist |

## Recommended use order

1. Start with `../templates/governance-spec.md`
2. Fill `../templates/governance.yaml`
3. Add fields from `data-contract-fragment.md`
4. Review scope with `dmbok-mapping.md`
5. Execute implementation using `../templates/implementation-checklist.md`

This MVP deliberately ships documentation-first assets before code-generation scripts.
