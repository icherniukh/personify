#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys

from package import check_target, build_target


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compatibility wrapper. Claude standalone copies are no longer authored; build the Claude package instead."
    )
    parser.add_argument("--check", action="store_true", help="Verify the generated Claude package is in sync.")
    args = parser.parse_args()
    if args.check:
        return 0 if check_target("claude") else 1
    build_target("claude")
    return 0


if __name__ == "__main__":
    sys.exit(main())
