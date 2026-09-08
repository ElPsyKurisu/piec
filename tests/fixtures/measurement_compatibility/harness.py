"""
Reusable characterization and compatibility test harness utilities for PIEC measurements.
"""

from __future__ import annotations

import inspect
import json
from pathlib import Path
from typing import Any, Sequence

import pandas as pd

MANIFEST_PATH = Path(__file__).parent / "manifest.json"


def load_manifest() -> dict[str, Any]:
    """Load the machine-readable compatibility manifest."""
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_manifest_family(family_name: str) -> dict[str, Any]:
    """Retrieve specifications for a single measurement family from the manifest."""
    manifest = load_manifest()
    families = manifest.get("families", {})
    if family_name not in families:
        raise KeyError(f"Family {family_name!r} not found in manifest. Available: {list(families.keys())}")
    return families[family_name]


def _assert_parameters_match(
    target: str,
    actual_params: Sequence[inspect.Parameter],
    expected_parameters: Sequence[dict[str, Any]],
    allowed_keyword_only: dict[str, Any] | None = None,
) -> None:
    """Preserve the legacy prefix; permit only explicitly approved optional keywords."""
    expected_names = [p["name"] for p in expected_parameters]
    legacy_params = actual_params[:len(expected_parameters)]
    assert [p.name for p in legacy_params] == expected_names, (
        f"Parameter order/names mismatch for {target}: "
        f"{[p.name for p in legacy_params]} != {expected_names}"
    )
    for actual, expected in zip(legacy_params, expected_parameters):
        assert actual.kind.name == expected["kind"], (
            f"Parameter {actual.name} kind mismatch on {target}"
        )
        expected_default = expected["default"]
        if expected_default == "__NO_DEFAULT__":
            assert actual.default is inspect.Parameter.empty, (
                f"Parameter {actual.name} on {target} must remain required"
            )
        else:
            assert actual.default == expected_default, (
                f"Parameter {actual.name} default mismatch on {target}: "
                f"{actual.default!r} != {expected_default!r}"
            )

    allowed = allowed_keyword_only or {}
    for extra in actual_params[len(expected_parameters):]:
        assert extra.name in allowed, f"Unapproved parameter {extra.name} on {target}"
        assert extra.kind is inspect.Parameter.KEYWORD_ONLY, (
            f"New parameter {extra.name} on {target} must be keyword-only"
        )
        assert extra.default is not inspect.Parameter.empty, (
            f"New parameter {extra.name} on {target} must be optional"
        )
        assert extra.default == allowed[extra.name], (
            f"New parameter {extra.name} default mismatch on {target}"
        )


def assert_constructor_signature_matches(
    cls: type,
    expected_parameters: Sequence[dict[str, Any]],
    *,
    allowed_keyword_only: dict[str, Any] | None = None,
) -> None:
    """Check legacy constructor parameters and explicitly approved additions."""
    actual = [p for p in inspect.signature(cls.__init__).parameters.values() if p.name != "self"]
    _assert_parameters_match(
        f"{cls.__name__}.__init__", actual, expected_parameters, allowed_keyword_only,
    )


def assert_public_methods_match(
    cls: type,
    expected_methods: dict[str, dict[str, Any]],
    *,
    allowed_keyword_only: dict[str, dict[str, Any]] | None = None,
) -> None:
    """Check legacy methods; allow only per-method approved optional keywords."""
    for method_name, method_spec in expected_methods.items():
        method = getattr(cls, method_name, None)
        assert callable(method), f"Class {cls.__name__} missing method {method_name!r}"
        actual = [p for p in inspect.signature(method).parameters.values() if p.name != "self"]
        _assert_parameters_match(
            f"{cls.__name__}.{method_name}", actual, method_spec.get("parameters", []),
            (allowed_keyword_only or {}).get(method_name),
        )


def assert_public_properties_match(
    cls: type,
    expected_properties: Sequence[str],
) -> None:
    """Verify that expected properties exist on the class."""
    for prop in expected_properties:
        assert hasattr(cls, prop), f"Class {cls.__name__} missing property {prop!r}"
        attr = getattr(cls, prop)
        assert isinstance(attr, property), f"Attribute {prop!r} on {cls.__name__} is not a property"


def assert_piec_csv_layout(path: str | Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Verify that a CSV file strictly obeys PIEC's one-row metadata / blank line / data table layout.

    Returns (metadata_df, data_df).
    """
    file_path = Path(path)
    assert file_path.is_file(), f"File {file_path} does not exist"

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    assert len(lines) >= 3, f"CSV file {file_path} too short to be valid PIEC standard (has {len(lines)} lines)"
    assert lines[2].strip() == "", f"Line 3 (index 2) of {file_path} must be a blank separator line, got: {lines[2]!r}"

    # Verify standard reader parses without error
    from piec.analysis.utilities import standard_csv_to_metadata_and_data
    metadata, data = standard_csv_to_metadata_and_data(str(file_path))

    assert isinstance(metadata, pd.DataFrame), "Metadata must be a DataFrame"
    assert len(metadata) == 1, f"Metadata must have exactly 1 row, got {len(metadata)}"
    assert isinstance(data, pd.DataFrame), "Data must be a DataFrame"

    return metadata, data


def assert_data_columns_match(
    df: pd.DataFrame,
    expected_columns: Sequence[str],
    exact_order: bool = True,
) -> None:
    """Verify DataFrame column names and ordering."""
    actual = list(df.columns)
    if exact_order:
        assert actual == list(expected_columns), (
            f"DataFrame columns/order mismatch:\n"
            f"  Actual:   {actual}\n"
            f"  Expected: {list(expected_columns)}"
        )
    else:
        missing = set(expected_columns) - set(actual)
        assert not missing, f"Missing required columns: {missing}"


def normalize_metadata_for_comparison(
    metadata_df: pd.DataFrame,
    volatile_keys: Sequence[str] | None = None,
) -> dict[str, Any]:
    """
    Extract a normalized dict of metadata parameters, excluding volatile runtime facts
    like timestamps, file paths, run IDs, and hardware identification strings.
    """
    default_volatile = {
        "timestamp", "run_id", "filename", "sourcemeter", "dmm",
        "lockin", "arduino", "calibrator", "osc", "awg",
    }
    exclude = default_volatile | set(volatile_keys or [])

    row = metadata_df.iloc[0].to_dict()
    return {k: v for k, v in row.items() if k not in exclude}
