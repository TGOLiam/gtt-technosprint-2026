import sys
from pathlib import Path

import yaml

from pipeline.config import DEFAULTS


def deep_merge(base, override):
    """Merge override into base. Nested dicts merge recursively."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_manifest(input_dir):
    yml = Path(input_dir) / "manifest.yml"
    if not yml.exists():
        print(f"Error: {yml} not found.")
        sys.exit(1)

    data = yaml.safe_load(yml.read_text(encoding="utf-8"))
    raw_defaults = data.get("defaults", {})
    files = data.get("files", [])

    if not files:
        print("Error: no files listed in manifest.yml")
        sys.exit(1)

    # Start from hardcoded defaults
    base = deep_merge(DEFAULTS, raw_defaults)

    resolved = []
    for entry in files:
        path_str = entry.get("path", "")
        if not path_str:
            print("Warning: entry missing 'path' field, skipping")
            continue

        file_path = Path(input_dir) / path_str
        if not file_path.exists():
            print(f"Warning: {path_str} not found, skipping")
            continue

        # Deep merge: base defaults → per-file overrides
        item = deep_merge(base, entry)
        item["_input_path"] = file_path
        item["_basename"] = file_path.stem

        # Ensure optional fields have defaults
        item.setdefault("dialect_label", "")
        item.setdefault("confidence", "inferred")
        item.setdefault("source_name", "")
        item.setdefault("source_type", "manual")

        resolved.append(item)

    if not resolved:
        print("Error: no valid files after resolving manifest")
        sys.exit(1)

    return resolved
