#!/usr/bin/env python3
"""Compare two TTFs after normalizing only the build-dependent head timestamp.

fontTools updates head.modified on save, which also changes the calculated
head table checksum and checkSumAdjustment. All other differences remain fatal.
"""
import argparse
from io import BytesIO
from pathlib import Path

from fontTools.ttLib import TTFont


def canonical_bytes(path: Path) -> bytes:
    font = TTFont(path, recalcTimestamp=False)
    try:
        font["head"].modified = 0
        output = BytesIO()
        font.save(output)
        return output.getvalue()
    finally:
        font.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("generated", type=Path)
    parser.add_argument("committed", type=Path)
    args = parser.parse_args()
    if canonical_bytes(args.generated) != canonical_bytes(args.committed):
        parser.exit(1, f"Font mismatch (beyond head.modified): {args.generated} vs {args.committed}\n")
    print(f"Verified: {args.committed}")


if __name__ == "__main__":
    main()
