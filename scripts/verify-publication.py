#!/usr/bin/env python3
"""Check the product source inventory and all fetched Git history."""
import argparse
from pathlib import Path
import sys
from publication_checks import ValidationError, validate_history, validate_source


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-only", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    try:
        validate_source(root)
        if not args.source_only:
            validate_history(root)
    except ValidationError as error:
        print(str(error), file=sys.stderr)
        return 1
    except (OSError, UnicodeError):
        print("source-read-failed: repository", file=sys.stderr)
        return 1
    print("OK: source inventory and requested email/identity checks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
