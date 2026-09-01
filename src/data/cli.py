"""Command-line entry points for local MIT-BIH data preparation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .mitbih import (
    DEFAULT_LEAD_MAP_PATH,
    DEFAULT_MANIFEST_PATH,
    DEFAULT_RAW_DIR,
    acquire,
    build_inventory,
)


def parser() -> argparse.ArgumentParser:
    argument_parser = argparse.ArgumentParser(description="Acquire and inventory MIT-BIH v1.0.0")
    subcommands = argument_parser.add_subparsers(dest="command", required=True)
    acquire_parser = subcommands.add_parser("acquire", help="Download missing source files")
    acquire_parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    inventory_parser = subcommands.add_parser("inventory", help="Write an inventory from local WFDB files")
    inventory_parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    inventory_parser.add_argument("--lead-map", type=Path, default=DEFAULT_LEAD_MAP_PATH)
    inventory_parser.add_argument("--output", type=Path, default=DEFAULT_MANIFEST_PATH)
    return argument_parser


def main() -> None:
    args = parser().parse_args()
    result = acquire(args.raw_dir) if args.command == "acquire" else build_inventory(
        args.raw_dir, args.lead_map, args.output
    )
    print(json.dumps(result, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
