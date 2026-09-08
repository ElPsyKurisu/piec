"""
Characterization tests verifying the compatibility manifest and test harness against the codebase.

Stage 0 Checkpoint 2a: manifest and characterization test harness.
"""

import importlib
import inspect
import subprocess
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from tests.fixtures.measurement_compatibility import (
    assert_family_interface,
    assert_constructor_signature_matches,
    assert_data_columns_match,
    assert_numerical_data_matches_reference,
    assert_piec_csv_layout,
    assert_public_methods_match,
    assert_public_properties_match,
    get_family_reference_observations,
    get_family_target_contract,
    get_manifest_family,
    get_migrated_families,
    get_old_to_new_column_mapping,
    is_family_migrated,
    load_manifest,
    normalize_metadata_for_comparison,
)


class TestManifestIntegrity:
    """Verify that the manifest is syntactically valid and covers all required families."""

    def test_manifest_loads_and_has_version(self):
        manifest = load_manifest()
        assert "schema_version" in manifest
        assert manifest["schema_version"] == "2.0.0"

    def test_manifest_records_pinned_baseline_commits(self):
        manifest = load_manifest()
        assert "baselines" in manifest
        baselines = manifest["baselines"]
        assert "master" in baselines
        assert "moke_feature" in baselines

        # Both commits must be 40-character hex strings
        for name, commit in baselines.items():
            assert len(commit) == 40, f"Baseline commit {name} must be a 40-char SHA: {commit}"
            # Verify commit exists in repository
            result = subprocess.run(
                ["git", "cat-file", "-t", commit],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0, f"Baseline commit {name} ({commit}) not found in git history"

    def test_manifest_contains_all_required_families(self):
        manifest = load_manifest()
        families = manifest.get("families", {})
        expected_families = [
            "IVSweep",
            "DiscreteWaveform",
            "HysteresisLoop",
            "ThreePulsePund",
            "MagnetoTransport",
            "AMR",
            "MokeMeasurement",
            "MokeSnapshot",
        ]
        for name in expected_families:
            assert name in families, f"Missing required family {name!r} in manifest"

    def test_manifest_has_compatibility_classifications(self):
        manifest = load_manifest()
        assert "compatibility_classifications" in manifest
        classifications = manifest["compatibility_classifications"]
        for key in ("preserved_behavior", "additive_api", "approved_safety_corrections"):
            assert key in classifications, f"Missing classification {key!r}"
            assert len(classifications[key]) > 0, f"Classification {key!r} must not be empty"

    def test_manifest_has_migrated_families_list(self):
        manifest = load_manifest()
        assert "migrated_families" in manifest
        assert isinstance(manifest["migrated_families"], list)
        names = manifest["migrated_families"]
        assert len(names) == len(set(names))
        assert set(names) <= set(manifest["families"])

    def test_manifest_has_standardization_principles(self):
        manifest = load_manifest()
        assert "standardization_principles" in manifest
        assert len(manifest["standardization_principles"]) >= 5
        assert "transitional_policy" in manifest

    def test_all_families_have_separated_reference_and_target_contracts(self):
        manifest = load_manifest()
        families = manifest.get("families", {})
        for name, spec in families.items():
            assert "reference_observations" in spec, f"Family {name!r} missing reference_observations"
            assert "target_contract" in spec, f"Family {name!r} missing target_contract"
            assert "old_to_new_column_mapping" in spec, f"Family {name!r} missing old_to_new_column_mapping"


class TestTargetContractSpecifications:
    """Verify that every family's target_contract satisfies the standardization rules in Section 3 and 7."""

    MEASUREMENT_FAMILIES = [
        "IVSweep",
        "DiscreteWaveform",
        "HysteresisLoop",
        "ThreePulsePund",
        "MagnetoTransport",
        "AMR",
        "MokeMeasurement",
    ]

    @pytest.mark.parametrize("family_name", MEASUREMENT_FAMILIES)
    def test_target_schema_canonical_names_and_version(self, family_name):
        target = get_family_target_contract(family_name)
        assert "measurement_schema" in target
        assert target["measurement_schema"] in {
            "iv_sweep",
            "discrete_waveform",
            "hysteresis",
            "three_pulse_pund",
            "amr",
            "moke",
        }
        assert target["measurement_schema_version"] == 1

    @pytest.mark.parametrize("family_name", MEASUREMENT_FAMILIES)
    def test_target_columns_are_plain_identifiers(self, family_name):
        target = get_family_target_contract(family_name)
        assert "ordered_columns" in target
        for col in target["ordered_columns"]:
            assert "(" not in col and ")" not in col, f"Column {col!r} contains units"
            assert "^" not in col and "*" not in col, f"Column {col!r} contains special punctuation"
            assert " " not in col, f"Column {col!r} contains spaces"

    @pytest.mark.parametrize("family_name", MEASUREMENT_FAMILIES)
    def test_target_column_units_map_all_ordered_columns(self, family_name):
        target = get_family_target_contract(family_name)
        assert "column_units" in target
        units = target["column_units"]
        for col in target["ordered_columns"]:
            assert col in units, f"Column {col!r} missing from column_units in {family_name}"
            assert units[col] is None or isinstance(units[col], str), (
                f"Unit for {col!r} in {family_name} must be a string or None"
            )

    @pytest.mark.parametrize("family_name", MEASUREMENT_FAMILIES)
    def test_old_to_new_column_mappings_are_valid(self, family_name):
        mapping = get_old_to_new_column_mapping(family_name)
        target = get_family_target_contract(family_name)
        all_target_cols = set(target["ordered_columns"]) | set(target.get("optional_columns", []))
        for old_col, new_col in mapping.items():
            assert new_col in all_target_cols, (
                f"Mapped target column {new_col!r} in {family_name} is not in target columns {all_target_cols}"
            )


class TestLiveCodeMatchesManifest:
    @pytest.mark.parametrize("family_name", list(load_manifest()["families"]))
    def test_live_interface_uses_migration_status(self, family_name):
        spec = get_manifest_family(family_name)
        module = importlib.import_module(spec["module"])
        cls = getattr(module, spec["class_name"])
        assert_family_interface(cls, family_name)


class TestHarnessUtilities:
    """Verify that test harness utilities function correctly and catch violations."""

    @pytest.mark.parametrize("constructor", [False, True])
    @pytest.mark.parametrize("signature,valid", [
        ("self, configure_lockin=True", True),
        ("self, configure_lockin=True, *, save=True", True),
        ("self, configure_lockin=True, *, save", False),
        ("self, configure_lockin=True, save=True", False),
        ("self, configure_lockin=True, *, save=False", False),
        ("self, configure_lockin=True, *, unknown=None", False),
        ("self, configure_lockin=False", False),
        ("self, *, configure_lockin=True", False),
        ("self, renamed=True", False),
        ("self", False),
        ("self, save=True, configure_lockin=True", False),
        ("self, configure_lockin=True, **kwargs", False),
    ])
    def test_signature_additions_preserve_legacy_calls(self, constructor, signature, valid):
        # These fixed source strings exercise real Python signature binding.
        namespace = {}
        name = "__init__" if constructor else "run_experiment"
        exec(f"def {name}({signature}): pass", namespace)
        cls = type("Example", (), {name: namespace[name]})
        expected = [{"name": "configure_lockin", "kind": "POSITIONAL_OR_KEYWORD", "default": True}]

        def check():
            if constructor:
                assert_constructor_signature_matches(cls, expected, allowed_keyword_only={"save": True})
            else:
                assert_public_methods_match(
                    cls, {name: {"parameters": expected}},
                    allowed_keyword_only={name: {"save": True}},
                )

        if valid:
            check()
            inspect.signature(namespace[name]).bind(object(), False)
        else:
            with pytest.raises(AssertionError):
                check()

    def test_moke_filename_grammar_matches_legacy_helper(self, tmp_path):
        from piec.analysis.utilities import create_measurement_filename

        spec = get_family_reference_observations("MokeMeasurement")
        actual = Path(create_measurement_filename(str(tmp_path), spec["mtype"]))
        assert actual.name == spec["filename_grammar"].format(index=0, mtype=spec["mtype"])
        assert actual.name == "0_moke_.csv"

    def test_piec_csv_layout_passes_for_valid_file(self):
        metadata = pd.DataFrame([{"param_a": 1.0, "param_b": "test"}])
        data = pd.DataFrame({"col_x": [1, 2, 3], "col_y": [4.0, 5.0, 6.0]})

        with tempfile.TemporaryDirectory() as tmp_dir:
            csv_path = Path(tmp_dir) / "valid.csv"
            from piec.analysis.utilities import metadata_and_data_to_csv
            metadata_and_data_to_csv(metadata, data, str(csv_path))

            meta_read, data_read = assert_piec_csv_layout(csv_path)
            assert len(meta_read) == 1
            assert len(data_read) == 3
            assert list(data_read.columns) == ["col_x", "col_y"]

    def test_piec_csv_layout_fails_when_blank_line_missing(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            corrupt_path = Path(tmp_dir) / "corrupt.csv"
            with open(corrupt_path, "w", encoding="utf-8") as f:
                f.write("meta_a,meta_b\n1,2\nno_blank_line\n1,2\n")

            with pytest.raises(AssertionError, match="must be a blank separator line"):
                assert_piec_csv_layout(corrupt_path)

    def test_data_columns_match_assertions(self):
        df = pd.DataFrame({"a": [1], "b": [2], "c": [3]})
        # Exact order passes
        assert_data_columns_match(df, ["a", "b", "c"], exact_order=True)

        # Wrong order fails under exact_order=True
        with pytest.raises(AssertionError, match="columns/order mismatch"):
            assert_data_columns_match(df, ["b", "a", "c"], exact_order=True)

        # Wrong order passes under exact_order=False
        assert_data_columns_match(df, ["b", "a", "c"], exact_order=False)

    def test_normalize_metadata_for_comparison(self):
        meta = pd.DataFrame([{
            "frequency": 1000.0,
            "amplitude": 1.0,
            "timestamp": 123456789.0,
            "filename": "fake/path.csv",
            "sourcemeter": "KEITHLEY INSTRUMENTS INC.",
        }])
        norm = normalize_metadata_for_comparison(meta)
        assert "frequency" in norm and norm["frequency"] == 1000.0
        assert "amplitude" in norm and norm["amplitude"] == 1.0
        assert "timestamp" not in norm
        assert "filename" not in norm
        assert "sourcemeter" not in norm

    def test_harness_query_helpers(self):
        contract = get_family_target_contract("IVSweep")
        assert contract["measurement_schema"] == "iv_sweep"

        obs = get_family_reference_observations("IVSweep")
        assert "constructor" in obs

        mapping = get_old_to_new_column_mapping("IVSweep")
        assert mapping == {"voltage (V)": "voltage", "current (A)": "current"}

        assert get_migrated_families() == load_manifest()["migrated_families"]
        assert is_family_migrated("IVSweep") == ("IVSweep" in get_migrated_families())

    def test_assert_numerical_data_matches_reference_success(self):
        ref_df = pd.DataFrame({"voltage (V)": [0.0, 0.5, 1.0], "current (A)": [0.0, 0.01, 0.02]})
        act_df = pd.DataFrame({"voltage": [0.0, 0.5, 1.0], "current": [0.0, 0.01, 0.02]})
        # Cross-schema comparison using old_to_new_column_mapping
        assert_numerical_data_matches_reference(act_df, ref_df, "IVSweep")

    def test_assert_numerical_data_matches_reference_detects_mismatch(self):
        ref_df = pd.DataFrame({"voltage (V)": [0.0, 0.5, 1.0], "current (A)": [0.0, 0.01, 0.02]})
        act_df = pd.DataFrame({"voltage": [0.0, 0.5, 1.0], "current": [0.0, 0.01, 0.99]})
        with pytest.raises(AssertionError, match="Numerical mismatch"):
            assert_numerical_data_matches_reference(act_df, ref_df, "IVSweep")

    def test_assert_numerical_data_matches_reference_detects_row_count_mismatch(self):
        ref_df = pd.DataFrame({"voltage (V)": [0.0, 0.5], "current (A)": [0.0, 0.01]})
        act_df = pd.DataFrame({"voltage": [0.0, 0.5, 1.0], "current": [0.0, 0.01, 0.02]})
        with pytest.raises(AssertionError, match="Row count mismatch"):
            assert_numerical_data_matches_reference(act_df, ref_df, "IVSweep")

    def test_assert_numerical_data_matches_reference_detects_missing_columns(self):
        ref_df = pd.DataFrame({"other_col": [1, 2]})
        act_df = pd.DataFrame({"another_col": [1, 2]})
        with pytest.raises(AssertionError, match="Missing actual column"):
            assert_numerical_data_matches_reference(act_df, ref_df, "IVSweep")
