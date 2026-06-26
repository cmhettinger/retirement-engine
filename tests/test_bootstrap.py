from pathlib import Path

import pytest
import yaml

from retirement_engine.bootstrap import configure_logging, initialize_application, main


def test_initialize_application_loads_config_and_creates_build_directory(tmp_path: Path) -> None:
    workbook = tmp_path / "example.xlsx"
    workbook.write_bytes(b"placeholder")
    output_directory = tmp_path / "build"
    config_path = write_config(tmp_path, workbook=workbook, output_directory=output_directory)

    context = initialize_application(config_path, log_level="WARNING")

    assert context.config.source_path == config_path.resolve()
    assert context.build_directory == output_directory.resolve()
    assert context.build_directory.is_dir()
    assert context.logger.name == "retirement_engine"


def test_initialize_application_accepts_nested_output_directory(tmp_path: Path) -> None:
    workbook = tmp_path / "example.xlsx"
    workbook.write_bytes(b"placeholder")
    output_directory = tmp_path / "nested" / "reports" / "build"
    config_path = write_config(tmp_path, workbook=workbook, output_directory=output_directory)

    context = initialize_application(config_path)

    assert context.build_directory == output_directory.resolve()
    assert context.build_directory.is_dir()


def test_configure_logging_rejects_unknown_log_level() -> None:
    with pytest.raises(ValueError, match="Unknown log level"):
        configure_logging("chatty")


def test_main_prints_version(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    workbook = tmp_path / "example.xlsx"
    workbook.write_bytes(b"placeholder")
    config_path = write_config(tmp_path, workbook=workbook, output_directory=tmp_path / "build")

    exit_code = main(["--config", str(config_path), "--version"])

    assert exit_code == 0
    assert capsys.readouterr().out.strip() == "0.1.0"


def write_config(tmp_path: Path, *, workbook: Path, output_directory: Path) -> Path:
    config_path = tmp_path / "config.yml"
    config_data = {
        "supported_workbook_version": "0.1.0",
        "default_workbook": str(workbook),
        "output_directory": str(output_directory),
        "reports": {
            "default_format": "pdf",
            "include_charts": True,
        },
    }
    config_path.write_text(yaml.safe_dump(config_data, sort_keys=False), encoding="utf-8")
    return config_path
