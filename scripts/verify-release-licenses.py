#!/usr/bin/env python3
"""Validate exact release contents, nested components, licenses and emails."""
import argparse
from pathlib import Path
import sys
from publication_checks import ValidationError, validate_release


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('version')
    parser.add_argument('--dist', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    try:
        validate_release(root, args.dist or root / 'dist', args.version)
    except ValidationError as error:
        print(str(error), file=sys.stderr)
        return 1
    except (OSError, UnicodeError):
        print('package-read-failed: dist', file=sys.stderr)
        return 1
    print('OK: exact product contents, licenses, notices, emails and checksums')
    return 0


if __name__ == '__main__':
    sys.exit(main())
