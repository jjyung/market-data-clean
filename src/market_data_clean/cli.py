from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Sequence

from market_data_clean import __version__
from market_data_clean.governance import (
    GovernanceValidationError,
    adapter_versions,
    append_audit_entry,
    build_manifest,
    build_ownership_map,
    build_quality_snapshot,
    build_retention_advisory,
    collect_governance_warnings,
    default_governance_config_path,
    generate_run_id,
    governance_template_text,
    isoformat_z,
    load_config,
    scan_retention,
    source_version_for_row,
    utc_now,
    write_config_copy,
    write_default_governance_config,
)
from market_data_clean.governance_schema import AuditEntry, GovernanceConfig, QualityConfig

REQUIRED_FIELDS = ["symbol", "timestamp", "open", "high", "low", "close", "volume"]
NUMERIC_FIELDS = ["open", "high", "low", "close", "volume"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="market-data-clean")
    parser.add_argument("--input", help="Input file path")
    parser.add_argument("--output", help="Output directory")
    parser.add_argument("--governance-config", default=str(default_governance_config_path()))
    parser.add_argument("--run-id")
    parser.add_argument("--governance-output")
    parser.add_argument("--no-governance", action="store_true")

    subparsers = parser.add_subparsers(dest="command")
    governance_parser = subparsers.add_parser("governance")
    governance_subparsers = governance_parser.add_subparsers(dest="governance_command", required=True)

    init_config_parser = governance_subparsers.add_parser("init-config")
    init_config_parser.add_argument("--output")

    retention_parser = governance_subparsers.add_parser("retention-check")
    retention_parser.add_argument("--config", required=True)
    retention_parser.add_argument("--data-dir", required=True)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "governance":
        if args.governance_command == "init-config":
            return run_init_config(args)
        if args.governance_command == "retention-check":
            return run_retention_check(args)

    if not args.input or not args.output:
        parser.error("the following arguments are required: --input, --output")

    try:
        return run_pipeline(args)
    except GovernanceValidationError as exc:
        print(str(exc), file=sys.stderr)
        return 2


def run_init_config(args: argparse.Namespace) -> int:
    try:
        if args.output:
            path = write_default_governance_config(Path(args.output), overwrite=False)
            print(f"Wrote governance template to {path}")
        else:
            print(governance_template_text(), end="")
        return 0
    except FileExistsError as exc:
        print(str(exc), file=sys.stderr)
        return 2


def run_retention_check(args: argparse.Namespace) -> int:
    config = load_config(Path(args.config))
    expired = scan_retention(config, Path(args.data_dir))
    if expired:
        print(json.dumps({"expired_artifacts": expired}, indent=2))
        return 1
    print(json.dumps({"expired_artifacts": []}, indent=2))
    return 0


def run_pipeline(args: argparse.Namespace) -> int:
    input_path = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    started_at = utc_now()
    rows = read_input_rows(input_path)
    cleaned_rows, rejected_rows, per_rule_counts, per_source_counts = validate_rows(rows)
    run_id = args.run_id or generate_run_id()

    governance_enabled = not args.no_governance
    governance_output = Path(args.governance_output) if args.governance_output else output_dir / "_governance"

    config_path = Path(args.governance_config)
    config = resolve_governance_config(config_path, governance_enabled)

    if governance_enabled:
        governance_output.mkdir(parents=True, exist_ok=True)
        enrich_rows_with_governance(cleaned_rows, rejected_rows, run_id, config)

    write_csv(output_dir / "cleaned.csv", cleaned_rows)
    write_csv(output_dir / "rejected.csv", rejected_rows)

    report = build_report(rows, cleaned_rows, rejected_rows, per_rule_counts, per_source_counts)

    if governance_enabled:
        config_copy_path = write_config_copy(config_path, governance_output) if config and config_path.exists() else None
        finished_at = utc_now()
        manifest = build_manifest(
            run_id=run_id,
            started_at=started_at,
            finished_at=finished_at,
            input_path=input_path,
            num_rows=len(rows),
            cleaned_rows=len(cleaned_rows),
            rejected_rows=len(rejected_rows),
            output_dir=output_dir,
            adapter_versions=adapter_versions(config, rows),
        )
        quality_snapshot = build_quality_snapshot(
            run_id=run_id,
            generated_at=finished_at,
            total_rows=len(rows),
            accepted_rows=len(cleaned_rows),
            rejected_rows=len(rejected_rows),
            per_rule_breakdown=per_rule_counts,
            per_source_breakdown=per_source_counts,
            rows=rows,
            quality_config=config.quality if config else QualityConfig(outlier_fields=["volume", "close"]),
        )
        append_audit_entry(
            governance_output / "audit_log.jsonl",
            AuditEntry(
                run_id=run_id,
                timestamp=isoformat_z(finished_at),
                input_path=str(input_path),
                output_dir=str(output_dir),
                num_input_rows=len(rows),
                num_cleaned=len(cleaned_rows),
                num_rejected=len(rejected_rows),
                cli_version=__version__,
                user=os.environ.get("USER", "unknown"),
            ),
        )
        write_json(governance_output / "manifest.json", asdict(manifest))
        write_json(governance_output / "quality.json", asdict(quality_snapshot))
        manifest_path = governance_output / "manifest.json"
        report["governance"] = {
            "run_id": run_id,
            "manifest_path": _display_path(manifest_path, output_dir),
            "ownership_map": build_ownership_map(config, rows),
            "governance_warnings": collect_governance_warnings(config, rows),
            "retention_advisory": build_retention_advisory(config, [input_path, *output_dir.rglob("*")]),
        }
        if config_copy_path:
            report["governance"]["config_used_path"] = _display_path(config_copy_path, output_dir)

    write_json(output_dir / "report.json", report)
    return 0


def resolve_governance_config(config_path: Path, governance_enabled: bool) -> GovernanceConfig | None:
    if not governance_enabled or not config_path.exists():
        return None
    return load_config(config_path)


def read_input_rows(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() != ".csv":
        raise ValueError("MVP input reader currently supports CSV files only")
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def validate_rows(
    rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int], dict[str, dict[str, int]]]:
    cleaned_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []
    per_rule_counts: dict[str, int] = {}
    per_source_counts: dict[str, dict[str, int]] = {}
    seen_keys: set[tuple[str, str]] = set()

    for line_number, row in enumerate(rows, start=2):
        source = str(row.get("source", "unknown") or "unknown")
        stats = per_source_counts.setdefault(source, {"total": 0, "accepted": 0, "rejected": 0})
        stats["total"] += 1

        reasons: list[str] = []
        missing_fields = [field for field in REQUIRED_FIELDS if not str(row.get(field, "")).strip()]
        if missing_fields:
            reasons.append("required_fields_missing")

        parsed_numeric: dict[str, float] = {}
        for field in NUMERIC_FIELDS:
            value = row.get(field)
            try:
                parsed_numeric[field] = float(value)
            except (TypeError, ValueError):
                if "required_fields_missing" not in reasons:
                    reasons.append("non_numeric_field")

        if row.get("timestamp") and not str(row.get("timestamp")).strip().endswith("Z"):
            reasons.append("timestamp_not_utc")
        if parsed_numeric.get("open", 0) < 0 or parsed_numeric.get("high", 0) < 0 or parsed_numeric.get("low", 0) < 0 or parsed_numeric.get("close", 0) < 0:
            reasons.append("negative_price")
        if parsed_numeric.get("volume", 0) < 0:
            reasons.append("negative_volume")
        if parsed_numeric and {"open", "high", "close"}.issubset(parsed_numeric) and parsed_numeric["high"] < max(parsed_numeric["open"], parsed_numeric["close"]):
            reasons.append("high_lt_max_open_close")
        if parsed_numeric and {"open", "low", "close"}.issubset(parsed_numeric) and parsed_numeric["low"] > min(parsed_numeric["open"], parsed_numeric["close"]):
            reasons.append("low_gt_min_open_close")

        dedupe_key = (str(row.get("symbol", "")), str(row.get("timestamp", "")))
        if dedupe_key in seen_keys:
            reasons.append("duplicate_symbol_timestamp")
        seen_keys.add(dedupe_key)

        normalized_row = dict(row)
        normalized_row["_line_number"] = line_number

        if reasons:
            for reason in reasons:
                per_rule_counts[reason] = per_rule_counts.get(reason, 0) + 1
            normalized_row["rejection_reasons"] = json.dumps(reasons)
            rejected_rows.append(normalized_row)
            stats["rejected"] += 1
        else:
            cleaned_rows.append(normalized_row)
            stats["accepted"] += 1

    return cleaned_rows, rejected_rows, per_rule_counts, per_source_counts


def enrich_rows_with_governance(
    cleaned_rows: list[dict[str, Any]], rejected_rows: list[dict[str, Any]], run_id: str, config: GovernanceConfig | None
) -> None:
    for row in cleaned_rows:
        source = str(row.get("source", "unknown") or "unknown")
        row["governance.run_id"] = run_id
        row["source_version"] = source_version_for_row(source, config)
        row["adapter_trace"] = json.dumps({"line_number": row.get("_line_number")})
        row["quality_score"] = 1.0
    for row in rejected_rows:
        source = str(row.get("source", "unknown") or "unknown")
        row["governance.run_id"] = run_id
        row["source_version"] = source_version_for_row(source, config)
        row["adapter_trace"] = json.dumps({"line_number": row.get("_line_number")})
        row["quality_score"] = 0.0


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    serialized_rows = [{k: v for k, v in row.items() if k != "_line_number"} for row in rows]
    fieldnames = sorted({key for row in serialized_rows for key in row.keys()})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(serialized_rows)


def build_report(
    rows: list[dict[str, Any]],
    cleaned_rows: list[dict[str, Any]],
    rejected_rows: list[dict[str, Any]],
    per_rule_counts: dict[str, int],
    per_source_counts: dict[str, dict[str, int]],
) -> dict[str, Any]:
    total_rows = len(rows)
    rejected = len(rejected_rows)
    return {
        "summary": {
            "total_rows": total_rows,
            "accepted_rows": len(cleaned_rows),
            "rejected_rows": rejected,
            "rejection_rate": rejected / total_rows if total_rows else 0.0,
        },
        "quality_summary": {
            "total_rows": total_rows,
            "accepted_rows": len(cleaned_rows),
            "rejected_rows": rejected,
            "rejection_rate": rejected / total_rows if total_rows else 0.0,
            "rules_broken": per_rule_counts,
            "per_source_rejection": per_source_counts,
        },
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _display_path(path: Path, base_dir: Path) -> str:
    try:
        return str(path.relative_to(base_dir))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    raise SystemExit(main())
