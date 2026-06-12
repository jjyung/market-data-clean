from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class OwnershipEntry:
    symbol: str
    source: str
    data_steward: str
    data_owner: str
    criticality: str
    classification: str
    data_domain: str
    description: str


@dataclass(slots=True)
class OwnershipConfig:
    defaults: dict[str, str]
    overrides: list[OwnershipEntry] = field(default_factory=list)


@dataclass(slots=True)
class RetentionPolicy:
    category: str
    retention_days: int
    archive_after_days: int | None
    deletion_after_days: int | None


@dataclass(slots=True)
class QualityConfig:
    outlier_z_score: float = 3.0
    max_rejection_rate: float = 0.10
    outlier_fields: list[str] = field(default_factory=list)


@dataclass(slots=True)
class AdapterConfig:
    expected_version: str
    source_label: str


@dataclass(slots=True)
class GovernanceConfig:
    version: str
    metadata: dict[str, Any]
    ownership: OwnershipConfig
    retention_policies: list[RetentionPolicy]
    quality: QualityConfig
    adapters: dict[str, AdapterConfig]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["retention"] = {"policies": payload.pop("retention_policies")}
        return payload


@dataclass(slots=True)
class RunManifest:
    run_id: str
    cli_version: str
    git_commit_hash: str | None
    started_at: str
    finished_at: str
    input: dict[str, Any]
    adapter_versions: dict[str, str]
    output: dict[str, Any]


@dataclass(slots=True)
class QualitySnapshot:
    run_id: str
    generated_at: str
    summary: dict[str, Any]
    per_rule_breakdown: dict[str, int]
    per_source_breakdown: dict[str, dict[str, int]]
    field_null_counts: dict[str, int]
    outlier_flags: dict[str, dict[str, float | int]]


@dataclass(slots=True)
class AuditEntry:
    run_id: str
    timestamp: str
    input_path: str
    output_dir: str
    num_input_rows: int
    num_cleaned: int
    num_rejected: int
    cli_version: str
    user: str
