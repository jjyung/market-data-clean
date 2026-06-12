from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import uuid
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, Iterable

try:
    import yaml  # type: ignore[import-not-found]
except ModuleNotFoundError:  # pragma: no cover - exercised indirectly
    yaml = None

from market_data_clean import __version__
from market_data_clean.governance_schema import (
    AdapterConfig,
    AuditEntry,
    GovernanceConfig,
    OwnershipConfig,
    OwnershipEntry,
    QualityConfig,
    QualitySnapshot,
    RetentionPolicy,
    RunManifest,
)

DEFAULT_REQUIRED_RETENTION_CATEGORIES = {"raw_input", "cleaned", "rejected", "report", "manifest"}
VALID_CRITICALITIES = {"low", "medium", "high"}
DEFAULT_GOVERNANCE_TEMPLATE_PATH = Path(__file__).resolve().parents[2] / "governance.yaml"


class GovernanceValidationError(ValueError):
    """Raised when governance config validation fails."""


def utc_now() -> datetime:
    return datetime.now(tz=UTC)


def isoformat_z(value: datetime) -> str:
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def generate_run_id() -> str:
    return str(uuid.uuid4())


def default_governance_config_path() -> Path:
    return DEFAULT_GOVERNANCE_TEMPLATE_PATH


def governance_template_text() -> str:
    return DEFAULT_GOVERNANCE_TEMPLATE_PATH.read_text(encoding="utf-8")


def write_default_governance_config(path: Path, overwrite: bool = False) -> Path:
    if path.exists() and not overwrite:
        raise FileExistsError(f"Refusing to overwrite existing governance config: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(governance_template_text(), encoding="utf-8")
    return path


def load_config(path: str | Path) -> GovernanceConfig:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Governance config not found: {config_path}")

    suffix = config_path.suffix.lower()
    raw_text = config_path.read_text(encoding="utf-8")

    if suffix in {".yaml", ".yml"}:
        payload = yaml.safe_load(raw_text) if yaml is not None else _simple_yaml_load(raw_text)
    elif suffix == ".json":
        payload = json.loads(raw_text)
    else:
        raise GovernanceValidationError(f"Unsupported governance config format: {config_path.suffix}")

    if not isinstance(payload, dict):
        raise GovernanceValidationError("Governance config must be a mapping/object at the top level")

    return _build_config(payload)


def _build_config(payload: dict[str, Any]) -> GovernanceConfig:
    errors: list[str] = []

    version = str(payload.get("version", "")).strip()
    metadata = payload.get("metadata") or {}
    ownership = payload.get("ownership") or {}
    defaults = ownership.get("defaults") or {}
    overrides = ownership.get("overrides") or []
    retention = payload.get("retention") or {}
    policies = retention.get("policies") or []
    quality = payload.get("quality") or {}
    adapters = payload.get("adapters") or {}

    if not version:
        errors.append("version is required")
    if not isinstance(metadata, dict):
        errors.append("metadata must be an object")
    if not isinstance(defaults, dict):
        errors.append("ownership.defaults must be an object")
    if not isinstance(overrides, list):
        errors.append("ownership.overrides must be a list")
    if not isinstance(policies, list):
        errors.append("retention.policies must be a list")
    if not isinstance(quality, dict):
        errors.append("quality must be an object")
    if not isinstance(adapters, dict):
        errors.append("adapters must be an object")

    ownership_entries: list[OwnershipEntry] = []
    for index, entry in enumerate(overrides if isinstance(overrides, list) else []):
        if not isinstance(entry, dict):
            errors.append(f"ownership.overrides[{index}] must be an object")
            continue
        required = [
            "symbol",
            "source",
            "data_steward",
            "data_owner",
            "criticality",
            "classification",
            "data_domain",
            "description",
        ]
        missing = [field for field in required if not str(entry.get(field, "")).strip()]
        if missing:
            errors.append(f"ownership.overrides[{index}] missing required fields: {', '.join(missing)}")
            continue
        if entry["criticality"] not in VALID_CRITICALITIES:
            errors.append(
                f"ownership.overrides[{index}].criticality must be one of {sorted(VALID_CRITICALITIES)}"
            )
        ownership_entries.append(OwnershipEntry(**{field: str(entry[field]) for field in required}))

    retention_entries: list[RetentionPolicy] = []
    seen_categories: set[str] = set()
    for index, policy in enumerate(policies if isinstance(policies, list) else []):
        if not isinstance(policy, dict):
            errors.append(f"retention.policies[{index}] must be an object")
            continue
        category = str(policy.get("category", "")).strip()
        if not category:
            errors.append(f"retention.policies[{index}].category is required")
            continue
        seen_categories.add(category)
        retention_days = _coerce_non_negative_int(policy.get("retention_days"), f"retention.policies[{index}].retention_days", errors)
        archive_after_days = _coerce_optional_non_negative_int(
            policy.get("archive_after_days"),
            f"retention.policies[{index}].archive_after_days",
            errors,
        )
        deletion_after_days = _coerce_optional_non_negative_int(
            policy.get("deletion_after_days"),
            f"retention.policies[{index}].deletion_after_days",
            errors,
        )
        if retention_days is None:
            continue
        retention_entries.append(
            RetentionPolicy(
                category=category,
                retention_days=retention_days,
                archive_after_days=archive_after_days,
                deletion_after_days=deletion_after_days,
            )
        )

    missing_categories = sorted(DEFAULT_REQUIRED_RETENTION_CATEGORIES - seen_categories)
    if missing_categories:
        errors.append(f"retention.policies missing required categories: {', '.join(missing_categories)}")

    quality_config = QualityConfig(
        outlier_z_score=float(quality.get("outlier_z_score", 3.0)),
        max_rejection_rate=float(quality.get("max_rejection_rate", 0.10)),
        outlier_fields=[str(item) for item in quality.get("outlier_fields", [])],
    )
    if quality_config.outlier_z_score <= 0:
        errors.append("quality.outlier_z_score must be > 0")
    if not 0 <= quality_config.max_rejection_rate <= 1:
        errors.append("quality.max_rejection_rate must be between 0.0 and 1.0")

    adapter_entries: dict[str, AdapterConfig] = {}
    for key, value in adapters.items():
        if not isinstance(value, dict):
            errors.append(f"adapters.{key} must be an object")
            continue
        expected_version = str(value.get("expected_version", "")).strip()
        source_label = str(value.get("source_label", key)).strip()
        if not expected_version:
            errors.append(f"adapters.{key}.expected_version is required")
            continue
        adapter_entries[str(key)] = AdapterConfig(expected_version=expected_version, source_label=source_label)

    if errors:
        raise GovernanceValidationError("Invalid governance config:\n- " + "\n- ".join(errors))

    return GovernanceConfig(
        version=version,
        metadata=metadata,
        ownership=OwnershipConfig(defaults={str(k): str(v) for k, v in defaults.items()}, overrides=ownership_entries),
        retention_policies=retention_entries,
        quality=quality_config,
        adapters=adapter_entries,
    )


def _coerce_non_negative_int(value: Any, field_name: str, errors: list[str]) -> int | None:
    try:
        converted = int(value)
    except (TypeError, ValueError):
        errors.append(f"{field_name} must be a non-negative integer, got {value!r}")
        return None
    if converted < 0:
        errors.append(f"{field_name} must be a non-negative integer, got {converted}")
        return None
    return converted


def _coerce_optional_non_negative_int(value: Any, field_name: str, errors: list[str]) -> int | None:
    if value is None:
        return None
    return _coerce_non_negative_int(value, field_name, errors)


def config_to_yaml(config: GovernanceConfig) -> str:
    if yaml is not None:
        return yaml.safe_dump(config.to_dict(), sort_keys=False, allow_unicode=True)
    return json.dumps(config.to_dict(), indent=2, ensure_ascii=False)


def _simple_yaml_load(text: str) -> Any:
    significant_lines: list[tuple[int, str]] = []
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        significant_lines.append((indent, stripped))
    if not significant_lines:
        return {}
    parsed, next_index = _parse_yaml_node(significant_lines, 0, significant_lines[0][0])
    if next_index != len(significant_lines):
        raise GovernanceValidationError("Unable to parse full YAML governance config")
    return parsed


def _parse_yaml_node(lines: list[tuple[int, str]], index: int, indent: int) -> tuple[Any, int]:
    current_indent, current_text = lines[index]
    if current_indent != indent:
        raise GovernanceValidationError("Invalid YAML indentation in governance config")
    if current_text.startswith("- "):
        return _parse_yaml_list(lines, index, indent)
    return _parse_yaml_dict(lines, index, indent)


def _parse_yaml_dict(lines: list[tuple[int, str]], index: int, indent: int) -> tuple[dict[str, Any], int]:
    payload: dict[str, Any] = {}
    while index < len(lines):
        current_indent, current_text = lines[index]
        if current_indent < indent:
            break
        if current_indent != indent or current_text.startswith("- "):
            break
        key, separator, remainder = current_text.partition(":")
        if not separator:
            raise GovernanceValidationError(f"Invalid YAML mapping entry: {current_text}")
        index += 1
        key = key.strip()
        remainder = remainder.strip()
        if remainder:
            payload[key] = _parse_yaml_scalar(remainder)
            continue
        if index < len(lines) and lines[index][0] > indent:
            payload[key], index = _parse_yaml_node(lines, index, lines[index][0])
        else:
            payload[key] = {}
    return payload, index


def _parse_yaml_list(lines: list[tuple[int, str]], index: int, indent: int) -> tuple[list[Any], int]:
    payload: list[Any] = []
    while index < len(lines):
        current_indent, current_text = lines[index]
        if current_indent < indent:
            break
        if current_indent != indent or not current_text.startswith("- "):
            break
        item_text = current_text[2:].strip()
        index += 1
        if not item_text:
            if index < len(lines) and lines[index][0] > indent:
                item, index = _parse_yaml_node(lines, index, lines[index][0])
            else:
                item = None
            payload.append(item)
            continue
        if ":" in item_text and not item_text.startswith(("'", '"')):
            key, _, remainder = item_text.partition(":")
            item: dict[str, Any] = {}
            key = key.strip()
            remainder = remainder.strip()
            if remainder:
                item[key] = _parse_yaml_scalar(remainder)
            elif index < len(lines) and lines[index][0] > indent:
                item[key], index = _parse_yaml_node(lines, index, lines[index][0])
            else:
                item[key] = {}
            if index < len(lines) and lines[index][0] > indent:
                extra, index = _parse_yaml_dict(lines, index, lines[index][0])
                item.update(extra)
            payload.append(item)
            continue
        payload.append(_parse_yaml_scalar(item_text))
    return payload, index


def _parse_yaml_scalar(value: str) -> Any:
    if value == "[]":
        return []
    if value == "{}":
        return {}
    if value in {"null", "Null", "NULL"}:
        return None
    if value in {"true", "True", "TRUE"}:
        return True
    if value in {"false", "False", "FALSE"}:
        return False
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def write_config_copy(config_path: Path, governance_output: Path) -> Path:
    destination = governance_output / f"config_used{config_path.suffix.lower()}"
    destination.write_text(config_path.read_text(encoding="utf-8"), encoding="utf-8")
    return destination


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def detect_git_commit_hash(repo_root: Path | None = None) -> str | None:
    root = repo_root or DEFAULT_GOVERNANCE_TEMPLATE_PATH.parent
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip() or None


def build_manifest(
    *,
    run_id: str,
    started_at: datetime,
    finished_at: datetime,
    input_path: Path,
    num_rows: int,
    cleaned_rows: int,
    rejected_rows: int,
    output_dir: Path,
    adapter_versions: dict[str, str],
) -> RunManifest:
    return RunManifest(
        run_id=run_id,
        cli_version=__version__,
        git_commit_hash=detect_git_commit_hash(),
        started_at=isoformat_z(started_at),
        finished_at=isoformat_z(finished_at),
        input={
            "path": str(input_path),
            "num_rows": num_rows,
            "sha256": file_sha256(input_path),
        },
        adapter_versions=adapter_versions,
        output={
            "cleaned_rows": cleaned_rows,
            "rejected_rows": rejected_rows,
            "output_path": str(output_dir),
        },
    )


def build_quality_snapshot(
    *,
    run_id: str,
    generated_at: datetime,
    total_rows: int,
    accepted_rows: int,
    rejected_rows: int,
    per_rule_breakdown: dict[str, int],
    per_source_breakdown: dict[str, dict[str, int]],
    rows: list[dict[str, Any]],
    quality_config: QualityConfig,
) -> QualitySnapshot:
    return QualitySnapshot(
        run_id=run_id,
        generated_at=isoformat_z(generated_at),
        summary={
            "total_rows": total_rows,
            "accepted_rows": accepted_rows,
            "rejected_rows": rejected_rows,
            "rejection_rate": rejected_rows / total_rows if total_rows else 0.0,
        },
        per_rule_breakdown=per_rule_breakdown,
        per_source_breakdown=per_source_breakdown,
        field_null_counts=compute_field_null_counts(rows),
        outlier_flags=compute_outlier_flags(rows, quality_config),
    )


def compute_field_null_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    fields: set[str] = set()
    for row in rows:
        fields.update(row.keys())
    counts: dict[str, int] = {field: 0 for field in sorted(fields)}
    for row in rows:
        for field in fields:
            value = row.get(field)
            if value in (None, ""):
                counts[field] += 1
    return counts


def compute_outlier_flags(rows: list[dict[str, Any]], quality_config: QualityConfig) -> dict[str, dict[str, float | int]]:
    flags: dict[str, dict[str, float | int]] = {}
    for field in quality_config.outlier_fields:
        values: list[float] = []
        for row in rows:
            value = row.get(field)
            try:
                if value not in (None, ""):
                    values.append(float(value))
            except (TypeError, ValueError):
                continue
        if len(values) < 2:
            flags[field] = {"z_score_threshold": quality_config.outlier_z_score, "flagged_rows": 0}
            continue
        avg = mean(values)
        deviation = pstdev(values)
        if math.isclose(deviation, 0.0):
            flags[field] = {"z_score_threshold": quality_config.outlier_z_score, "flagged_rows": 0}
            continue
        flagged = sum(1 for value in values if abs((value - avg) / deviation) > quality_config.outlier_z_score)
        flags[field] = {"z_score_threshold": quality_config.outlier_z_score, "flagged_rows": flagged}
    return flags


def append_audit_entry(audit_log_path: Path, entry: AuditEntry) -> None:
    audit_log_path.parent.mkdir(parents=True, exist_ok=True)
    with audit_log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")


def source_version_for_row(source: str, config: GovernanceConfig | None) -> str:
    if config and source in config.adapters:
        return f"{source}:{config.adapters[source].expected_version}"
    return f"{source}:unknown"


def adapter_versions(config: GovernanceConfig | None, rows: Iterable[dict[str, Any]]) -> dict[str, str]:
    sources = sorted({str(row.get("source", "unknown") or "unknown") for row in rows})
    versions: dict[str, str] = {}
    for source in sources:
        versions[source] = source_version_for_row(source, config).split(":", 1)[1]
    return versions


def ownership_entry_for(config: GovernanceConfig, symbol: str, source: str) -> OwnershipEntry | None:
    for entry in config.ownership.overrides:
        if entry.symbol == symbol and entry.source == source:
            return entry
    return None


def build_ownership_map(config: GovernanceConfig | None, rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, str]]:
    if config is None:
        return {}
    mapping: dict[str, dict[str, str]] = {}
    defaults = config.ownership.defaults
    for row in rows:
        source = str(row.get("source", "unknown") or "unknown")
        symbol = str(row.get("symbol", "") or "")
        entry = ownership_entry_for(config, symbol, source)
        mapping[source] = {
            "steward": entry.data_steward if entry else defaults.get("data_steward", ""),
            "owner": entry.data_owner if entry else defaults.get("data_owner", ""),
        }
    return mapping


def collect_governance_warnings(config: GovernanceConfig | None, rows: Iterable[dict[str, Any]]) -> list[str]:
    if config is None:
        return []
    seen: set[tuple[str, str]] = set()
    warnings: list[str] = []
    for row in rows:
        source = str(row.get("source", "unknown") or "unknown")
        symbol = str(row.get("symbol", "") or "")
        key = (symbol, source)
        if key in seen:
            continue
        seen.add(key)
        if not ownership_entry_for(config, symbol, source):
            warnings.append(f"symbol '{symbol}' from source '{source}' has no ownership entry found")
    return warnings


def determine_category(path: Path) -> str | None:
    parts = {part.lower() for part in path.parts}
    name = path.name.lower()
    if name == "manifest.json":
        return "manifest"
    if name == "report.json":
        return "report"
    if name == "cleaned.csv":
        return "cleaned"
    if name == "rejected.csv":
        return "rejected"
    if "raw_input" in parts or "raw" in parts or "input" in name:
        return "raw_input"
    return None


def build_retention_advisory(config: GovernanceConfig | None, paths: Iterable[Path], *, now: datetime | None = None) -> dict[str, list[dict[str, Any]]]:
    if config is None:
        return {"expired_artifacts": []}
    policies = {policy.category: policy for policy in config.retention_policies}
    current = now or utc_now()
    expired: list[dict[str, Any]] = []
    for path in paths:
        if not path.exists() or path.is_dir():
            continue
        category = determine_category(path)
        if category is None or category not in policies:
            continue
        policy = policies[category]
        age_days = int((current - datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)).total_seconds() // 86400)
        if age_days <= policy.retention_days:
            continue
        expired.append(
            {
                "category": category,
                "path": str(path),
                "age_days": age_days,
                "policy_days": policy.retention_days,
                "days_overdue": age_days - policy.retention_days,
                "action": "archive_or_delete",
            }
        )
    return {"expired_artifacts": sorted(expired, key=lambda item: item["path"])}


def scan_retention(config: GovernanceConfig, data_dir: Path) -> list[dict[str, Any]]:
    advisory = build_retention_advisory(config, data_dir.rglob("*"))
    return advisory["expired_artifacts"]
