from pathlib import Path

import pytest
import yaml

from retirement_engine.config import EXAMPLE_CONFIG_PATH, ConfigError, load_config
from retirement_engine.version import __version__


def test_load_default_config() -> None:
    config = load_config()

    assert config.application_version == __version__ == "0.1.0"
    assert config.supported_workbook_version == "0.1.0"
    assert (
        config.default_workbook
        == (config.project_root / "resources/workbooks/example.xlsx").resolve()
    )
    assert config.default_workbook.is_file()
    assert config.output_directory == (config.project_root / "build").resolve()
    assert config.reports.default_format == "pdf"
    assert config.reports.include_charts is True


def test_load_config_uses_runtime_application_version(tmp_path: Path) -> None:
    workbook = tmp_path / "example.xlsx"
    workbook.write_bytes(b"placeholder")
    config_path = write_config(tmp_path, workbook=workbook, application_version="9.9.9")

    config = load_config(config_path)

    assert config.application_version == __version__ == "0.1.0"


def test_load_example_config() -> None:
    config = load_config(EXAMPLE_CONFIG_PATH)

    assert config.source_path == (config.project_root / EXAMPLE_CONFIG_PATH).resolve()
    assert (
        config.default_workbook
        == (config.project_root / "resources/workbooks/example.xlsx").resolve()
    )


def test_load_config_requires_existing_default_workbook(tmp_path: Path) -> None:
    config_path = write_config(tmp_path, workbook=tmp_path / "missing.xlsx")

    with pytest.raises(ConfigError, match="default_workbook"):
        load_config(config_path)


def test_load_config_validates_report_format(tmp_path: Path) -> None:
    workbook = tmp_path / "example.xlsx"
    workbook.write_bytes(b"placeholder")
    config_path = write_config(tmp_path, workbook=workbook, report_format="spreadsheet")

    with pytest.raises(ConfigError, match="reports.default_format"):
        load_config(config_path)


def write_config(
    tmp_path: Path,
    *,
    workbook: Path,
    application_version: str | None = None,
    report_format: str = "pdf",
) -> Path:
    config_path = tmp_path / "config.yml"
    config_data = {
        "supported_workbook_version": "0.1.0",
        "default_workbook": str(workbook),
        "output_directory": str(tmp_path / "build"),
        "reports": {
            "default_format": report_format,
            "include_charts": True,
        },
    }
    if application_version is not None:
        config_data["application_version"] = application_version

    config_path.write_text(
        yaml.safe_dump(
            config_data,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return config_path
