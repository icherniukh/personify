#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys

from package import check_target, build_target


def main() -> int:
    parser = argparse.ArgumentParser(description="Compatibility wrapper for the promptonality Gemini package build.")
    parser.add_argument("--check", action="store_true", help="Verify the generated Gemini package is in sync.")
    args = parser.parse_args()
    if args.check:
        return 0 if check_target("gemini") else 1
    build_target("gemini")
    return 0


if __name__ == "__main__":
    sys.exit(main())
