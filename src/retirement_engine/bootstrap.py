"""Application bootstrap helpers."""

from __future__ import annotations

import argparse
import logging
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from retirement_engine.config import DEFAULT_CONFIG_PATH, AppConfig, load_config

LOGGER_NAME = "retirement_engine"
DEFAULT_LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


@dataclass(frozen=True)
class ApplicationContext:
    """Runtime state shared by CLI commands."""

    config: AppConfig
    logger: logging.Logger
    build_directory: Path


def initialize_application(
    config_path: str | Path = DEFAULT_CONFIG_PATH,
    *,
    log_level: str | int = logging.INFO,
) -> ApplicationContext:
    """Load configuration and prepare common runtime directories."""

    resolved_log_level = _resolve_log_level(log_level)
    configure_logging(resolved_log_level)

    config = load_config(config_path)
    config.output_directory.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(LOGGER_NAME)
    logger.debug("Loaded configuration from %s", config.source_path)
    logger.debug("Using build directory %s", config.output_directory)

    return ApplicationContext(
        config=config,
        logger=logger,
        build_directory=config.output_directory,
    )


def configure_logging(log_level: str | int = logging.INFO) -> None:
    """Configure package logging without adding duplicate handlers."""

    resolved_log_level = _resolve_log_level(log_level)
    package_logger = logging.getLogger(LOGGER_NAME)
    package_logger.setLevel(resolved_log_level)

    if not logging.getLogger().handlers:
        logging.basicConfig(level=resolved_log_level, format=DEFAULT_LOG_FORMAT)
    else:
        logging.getLogger().setLevel(resolved_log_level)


def main(argv: Sequence[str] | None = None) -> int:
    """Bootstrap the application from the command line."""

    parser = argparse.ArgumentParser(prog="retirement-engine")
    parser.add_argument(
        "--config",
        default=DEFAULT_CONFIG_PATH,
        help="Path to the application configuration file.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level to use during startup.",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Print the application version and exit.",
    )
    args = parser.parse_args(argv)

    context = initialize_application(args.config, log_level=args.log_level)

    if args.version:
        print(context.config.application_version)
        return 0

    print(
        "Retirement Engine "
        f"{context.config.application_version} initialized. "
        f"Output directory: {context.build_directory}"
    )
    return 0


def _resolve_log_level(log_level: str | int) -> int:
    if isinstance(log_level, int):
        return log_level

    level_name = log_level.strip().upper()
    level = logging.getLevelName(level_name)
    if not isinstance(level, int):
        raise ValueError(f"Unknown log level: {log_level}")
    return level


if __name__ == "__main__":
    raise SystemExit(main())
