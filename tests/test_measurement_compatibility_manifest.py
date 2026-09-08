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
    assert_constructor_signature_matches,
    assert_data_columns_match,
    assert_piec_csv_layout,
    assert_public_methods_match,
    assert_public_properties_match,
    get_manifest_family,
    load_manifest,
    normalize_metadata_for_comparison,
)


class TestManifestIntegrity:
    """Verify that the manifest is syntactically valid and covers all required families."""

    def test_manifest_loads_and_has_version(self):
        manifest = load_manifest()
        assert "schema_version" in manifest
        assert manifest["schema_version"] == "1.0.0"

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


class TestLiveCodeMatchesManifest:
    """Characterize and assert that the current production code exactly matches the manifest."""

    @pytest.mark.parametrize(
        "family_name",
        [
            "IVSweep",
            "DiscreteWaveform",
            "HysteresisLoop",
            "ThreePulsePund",
            "MagnetoTransport",
            "AMR",
            "MokeMeasurement",
            "MokeSnapshot",
        ],
    )
    def test_family_can_be_imported(self, family_name):
        spec = get_manifest_family(family_name)
        module = importlib.import_module(spec["module"])
        assert hasattr(module, spec["class_name"]), (
            f"Module {spec['module']} has no attribute {spec['class_name']}"
        )

    @pytest.mark.parametrize(
        "family_name",
        [
            "IVSweep",
            "DiscreteWaveform",
            "HysteresisLoop",
            "ThreePulsePund",
            "MagnetoTransport",
            "AMR",
            "MokeMeasurement",
            "MokeSnapshot",
        ],
    )
    def test_constructor_signature_matches_manifest(self, family_name):
        spec = get_manifest_family(family_name)
        module = importlib.import_module(spec["module"])
        cls = getattr(module, spec["class_name"])
        assert_constructor_signature_matches(cls, spec["constructor"]["parameters"])

    @pytest.mark.parametrize(
        "family_name",
        [
            "IVSweep",
            "DiscreteWaveform",
            "HysteresisLoop",
            "ThreePulsePund",
            "MagnetoTransport",
            "AMR",
            "MokeMeasurement",
        ],
    )
    def test_public_methods_match_manifest(self, family_name):
        spec = get_manifest_family(family_name)
        module = importlib.import_module(spec["module"])
        cls = getattr(module, spec["class_name"])
        assert_public_methods_match(
            cls, spec["public_methods"],
            allowed_keyword_only={
                "run_experiment": {"on_update": None, "save": True, "save_partial": None},
            },
        )

    @pytest.mark.parametrize(
        "family_name",
        [
            "IVSweep",
            "DiscreteWaveform",
            "HysteresisLoop",
            "ThreePulsePund",
            "MagnetoTransport",
            "AMR",
            "MokeMeasurement",
        ],
    )
    def test_public_properties_match_manifest(self, family_name):
        spec = get_manifest_family(family_name)
        module = importlib.import_module(spec["module"])
        cls = getattr(module, spec["class_name"])
        assert_public_properties_match(cls, spec.get("properties", []))

    def test_amr_module_reexports(self):
        manifest = load_manifest()
        reexports = manifest["module_reexports"]["piec.measurement.amr"]
        mod = importlib.import_module("piec.measurement.amr")

        assert hasattr(mod, "__all__"), "piec.measurement.amr must define __all__"
        assert set(mod.__all__) == set(reexports["exported_names"]), (
            f"Exported names mismatch in piec.measurement.amr: {mod.__all__} != {reexports['exported_names']}"
        )
        for name in reexports["exported_names"]:
            assert hasattr(mod, name), f"piec.measurement.amr is missing re-export: {name!r}"

    def test_moke_snapshot_dataclass(self):
        spec = get_manifest_family("MokeSnapshot")
        from piec.measurement.moke import MokeSnapshot

        fields = [f.name for f in inspect.signature(MokeSnapshot).parameters.values()]
        assert fields == spec["fields"]


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

        spec = get_manifest_family("MokeMeasurement")
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
