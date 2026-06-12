from __future__ import annotations

import csv
import json
import os
from pathlib import Path

import pytest

from market_data_clean.cli import main
from market_data_clean.governance import GovernanceValidationError, append_audit_entry, load_config
from market_data_clean.governance_schema import AuditEntry


FIXTURES = Path(__file__).parent / "fixtures"


def test_load_valid_governance_config() -> None:
    config = load_config(FIXTURES / "governance_valid.yaml")
    assert config.version == "1.0"
    assert config.quality.max_rejection_rate == 0.25
    assert config.ownership.overrides[0].symbol == "TX"


def test_invalid_governance_config_rejected() -> None:
    with pytest.raises(GovernanceValidationError) as exc:
        load_config(FIXTURES / "governance_invalid_retention.yaml")
    assert "retention.policies[0].retention_days" in str(exc.value)


def test_audit_log_append_behavior(tmp_path: Path) -> None:
    audit_path = tmp_path / "audit_log.jsonl"
    append_audit_entry(
        audit_path,
        AuditEntry(
            run_id="run-1",
            timestamp="2026-06-12T00:00:00Z",
            input_path="input-a.csv",
            output_dir="out-a",
            num_input_rows=1,
            num_cleaned=1,
            num_rejected=0,
            cli_version="0.1.0",
            user="tester",
        ),
    )
    append_audit_entry(
        audit_path,
        AuditEntry(
            run_id="run-2",
            timestamp="2026-06-12T00:01:00Z",
            input_path="input-b.csv",
            output_dir="out-b",
            num_input_rows=2,
            num_cleaned=1,
            num_rejected=1,
            cli_version="0.1.0",
            user="tester",
        ),
    )
    lines = audit_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["run_id"] == "run-1"
    assert json.loads(lines[1])["run_id"] == "run-2"


def test_init_config_command(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    output_path = tmp_path / "governance.yaml"
    exit_code = main(["governance", "init-config", "--output", str(output_path)])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert output_path.exists()
    assert "Wrote governance template" in captured.out


def test_retention_check_command(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    raw_dir = tmp_path / "raw_input"
    raw_dir.mkdir()
    expired_file = raw_dir / "old-input.csv"
    expired_file.write_text("x\n", encoding="utf-8")
    old_time = 1_700_000_000
    os.utime(expired_file, (old_time, old_time))

    exit_code = main(
        [
            "governance",
            "retention-check",
            "--config",
            str(FIXTURES / "governance_valid.yaml"),
            "--data-dir",
            str(tmp_path),
        ]
    )
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "old-input.csv" in captured.out


def test_main_cli_writes_governance_artifacts_when_enabled(tmp_path: Path) -> None:
    input_path = tmp_path / "input.csv"
    write_input_csv(
        input_path,
        [
            {
                "symbol": "TX",
                "timestamp": "2026-06-12T08:00:00Z",
                "open": "100",
                "high": "101",
                "low": "99",
                "close": "100.5",
                "volume": "10",
                "source": "finmind",
            },
            {
                "symbol": "TXFR1",
                "timestamp": "2026-06-12T08:00:00Z",
                "open": "100",
                "high": "99",
                "low": "101",
                "close": "100.5",
                "volume": "10",
                "source": "sinopac",
            },
        ],
    )

    output_dir = tmp_path / "out"
    exit_code = main(
        [
            "--input",
            str(input_path),
            "--output",
            str(output_dir),
            "--governance-config",
            str(FIXTURES / "governance_valid.yaml"),
            "--run-id",
            "test-run-id",
        ]
    )

    assert exit_code == 0
    governance_dir = output_dir / "_governance"
    assert (governance_dir / "manifest.json").exists()
    assert (governance_dir / "quality.json").exists()
    assert (governance_dir / "audit_log.jsonl").exists()
    assert (governance_dir / "config_used.yaml").exists()

    report = json.loads((output_dir / "report.json").read_text(encoding="utf-8"))
    assert report["governance"]["run_id"] == "test-run-id"
    assert "quality_summary" in report
    assert report["governance"]["governance_warnings"]

    with (output_dir / "cleaned.csv").open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["governance.run_id"] == "test-run-id"
    assert rows[0]["source_version"] == "finmind:finmind-api-v4"


def write_input_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
