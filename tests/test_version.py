from importlib.metadata import version

from retirement_engine.version import __version__


def test_runtime_version() -> None:
    assert __version__ == "0.1.0"


def test_package_version_matches_runtime_version() -> None:
    assert version("retirement-engine") == __version__
