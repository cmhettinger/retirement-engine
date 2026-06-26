"""Application version helpers."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

PACKAGE_NAME = "retirement-engine"


def _version_from_repo_file() -> str | None:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "VERSION"
        if candidate.is_file():
            return candidate.read_text(encoding="utf-8").strip()
    return None


def _version_from_package_metadata() -> str:
    try:
        return version(PACKAGE_NAME)
    except PackageNotFoundError as error:
        raise RuntimeError("Unable to determine retirement-engine version.") from error


__version__ = _version_from_repo_file() or _version_from_package_metadata()
