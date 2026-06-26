"""Configuration loading and validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from retirement_engine.version import __version__

DEFAULT_CONFIG_PATH = Path("env/config.yml")
SUPPORTED_REPORT_FORMATS = frozenset({"console", "html", "pdf", "text"})


class ConfigError(ValueError):
    """Raised when application configuration is missing or invalid."""


@dataclass(frozen=True)
class ReportConfig:
    default_format: str
    include_charts: bool


@dataclass(frozen=True)
class AppConfig:
    application_version: str
    supported_workbook_version: str
    default_workbook: Path
    output_directory: Path
    reports: ReportConfig
    source_path: Path
    project_root: Path


def load_config(path: str | Path = DEFAULT_CONFIG_PATH) -> AppConfig:
    """Load and validate the application configuration file."""

    config_path = Path(path).expanduser()
    if not config_path.is_absolute():
        config_path = _project_root() / config_path
    config_path = config_path.resolve()

    if not config_path.is_file():
        raise ConfigError(f"Configuration file does not exist: {config_path}")

    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise ConfigError("Configuration file must contain a mapping.")

    return _parse_config(raw, source_path=config_path, project_root=_project_root())


def _parse_config(raw: dict[str, Any], source_path: Path, project_root: Path) -> AppConfig:
    supported_workbook_version = _required_string(raw, "supported_workbook_version")
    default_workbook = _required_existing_path(raw, "default_workbook", project_root)
    output_directory = _required_path(raw, "output_directory", project_root)

    reports_raw = raw.get("reports")
    if not isinstance(reports_raw, dict):
        raise ConfigError("reports must be a mapping.")

    default_format = _required_string(reports_raw, "default_format")
    if default_format not in SUPPORTED_REPORT_FORMATS:
        formats = ", ".join(sorted(SUPPORTED_REPORT_FORMATS))
        raise ConfigError(f"reports.default_format must be one of: {formats}.")

    include_charts = reports_raw.get("include_charts")
    if not isinstance(include_charts, bool):
        raise ConfigError("reports.include_charts must be true or false.")

    return AppConfig(
        application_version=__version__,
        supported_workbook_version=supported_workbook_version,
        default_workbook=default_workbook,
        output_directory=output_directory,
        reports=ReportConfig(default_format=default_format, include_charts=include_charts),
        source_path=source_path,
        project_root=project_root,
    )


def _required_string(raw: dict[str, Any], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{key} must be a non-empty string.")
    return value.strip()


def _required_path(raw: dict[str, Any], key: str, project_root: Path) -> Path:
    value = _required_string(raw, key)
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = project_root / path
    return path.resolve()


def _required_existing_path(raw: dict[str, Any], key: str, project_root: Path) -> Path:
    path = _required_path(raw, key, project_root)
    if not path.is_file():
        raise ConfigError(f"{key} does not point to an existing file: {path}")
    return path


def _project_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "VERSION").is_file() and (parent / "env" / "config.yml").is_file():
            return parent
    return Path.cwd().resolve()
