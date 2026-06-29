from __future__ import annotations

import argparse

from retirement_engine.reports.core import __version__


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m retirement_engine.reports.core")
    parser.add_argument("--version", action="store_true", help="Print package version.")
    args = parser.parse_args()

    if args.version:
        print(__version__)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
