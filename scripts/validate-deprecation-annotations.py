#!/usr/bin/env python3
"""
Validate deprecation annotations in OpenAPI specs.

This script validates that deprecated OpenAPI operations are properly marked
with `deprecated: true`. The Controller POC uses view-level headers without
requiring OpenAPI extensions, but the spec should still be marked for
documentation and tooling purposes.

Part of the Controller deprecation header POC (ANSTRAT-2346).

Usage:
    python3 validate-deprecation-annotations.py --spec-paths "schema.json"
    python3 validate-deprecation-annotations.py --spec-paths "*.json"
"""

import argparse
import glob
import json
import sys
from pathlib import Path

# HTTP methods to check
HTTP_METHODS = ("get", "put", "post", "delete", "patch", "options", "head", "trace")


def validate_spec(spec_path):
    """
    Validate a single OpenAPI spec file.

    Args:
        spec_path: Path to the OpenAPI spec file (JSON or YAML)

    Returns:
        Dict with counts of deprecated operations
    """
    stats = {
        'total_operations': 0,
        'deprecated_operations': 0,
        'errors': []
    }

    try:
        spec = load_spec(spec_path)
    except Exception as e:
        stats['errors'].append(f"Failed to parse {spec_path}: {e}")
        return stats

    paths = spec.get("paths", {})
    if not paths:
        # Empty spec or no paths - skip silently
        return stats

    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue

        for method in HTTP_METHODS:
            operation = path_item.get(method)
            if not operation or not isinstance(operation, dict):
                continue

            stats['total_operations'] += 1

            if operation.get("deprecated"):
                stats['deprecated_operations'] += 1

    return stats


def load_spec(spec_path):
    """
    Load an OpenAPI spec file (JSON or YAML).

    Args:
        spec_path: Path to the spec file

    Returns:
        Parsed spec as a dict
    """
    content = Path(spec_path).read_text()

    # Try JSON first
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Try YAML if available
    try:
        import yaml
        return yaml.safe_load(content)
    except ImportError:
        raise ValueError(f"Could not parse {spec_path}: not valid JSON and PyYAML not available")
    except yaml.YAMLError as e:
        raise ValueError(f"Could not parse {spec_path}: {e}")


def emit_summary(all_stats, spec_files):
    """
    Emit a summary table of validation results.

    Args:
        all_stats: Dict mapping spec file paths to stats dicts
        spec_files: List of all spec files checked
    """
    print("\n" + "=" * 80)
    print("OPENAPI DEPRECATION ANNOTATION SUMMARY")
    print("=" * 80)

    total_ops = sum(s['total_operations'] for s in all_stats.values())
    total_deprecated = sum(s['deprecated_operations'] for s in all_stats.values())

    print(f"Total operations: {total_ops}")
    print(f"Deprecated operations: {total_deprecated}")
    print(f"Checked {len(spec_files)} spec file(s)")

    # Show breakdown by file
    for spec_path, stats in all_stats.items():
        if stats['deprecated_operations'] > 0:
            print(f"\n{spec_path}:")
            print(f"  {stats['deprecated_operations']} deprecated / {stats['total_operations']} total")

        # Show errors if any
        if stats['errors']:
            print(f"\nErrors in {spec_path}:")
            for error in stats['errors']:
                print(f"  - {error}")

    # Check if any errors occurred
    has_errors = any(s['errors'] for s in all_stats.values())
    if has_errors:
        print("\n✗ Validation failed due to errors")
        return False
    else:
        print("\n✓ Validation complete")
        return True


def main():
    parser = argparse.ArgumentParser(
        description="Validate deprecation annotations in OpenAPI specs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --spec-paths "schema.json"
  %(prog)s --spec-paths "*.json"
  %(prog)s --spec-paths "specs/**/*.yaml"
        """
    )
    parser.add_argument(
        "--spec-paths",
        required=True,
        help="Glob pattern or file path for OpenAPI spec files (e.g., '*.json', 'schema.json')"
    )
    args = parser.parse_args()

    # Expand glob pattern
    spec_files = glob.glob(args.spec_paths, recursive=True)

    if not spec_files:
        print(f"No spec files found matching pattern: {args.spec_paths}")
        sys.exit(1)

    # Validate each spec
    all_stats = {}
    for spec_path in spec_files:
        stats = validate_spec(spec_path)
        all_stats[spec_path] = stats

    # Emit summary
    success = emit_summary(all_stats, spec_files)

    # Exit with error code if validation failed
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
