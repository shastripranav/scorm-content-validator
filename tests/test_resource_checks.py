import zipfile

from scorm_validator.checks.resources import run_resource_checks
from scorm_validator.manifest_parser import parse_manifest


class TestResourceChecks:
    def test_all_files_present(self, valid_scorm12_zip):
        with zipfile.ZipFile(valid_scorm12_zip) as zf:
            manifest = parse_manifest(zf.read("imsmanifest.xml"))
            results = run_resource_checks(manifest, zf)
        errors = [r for r in results if not r.passed and r.severity == "error"]
        assert len(errors) == 0

    def test_missing_files_detected(self, missing_files_zip):
        with zipfile.ZipFile(missing_files_zip) as zf:
            manifest = parse_manifest(zf.read("imsmanifest.xml"))
            results = run_resource_checks(manifest, zf)
        errors = [r for r in results if not r.passed and r.severity == "error"]
        assert len(errors) > 0

    def test_orphan_resource_warning(self, orphan_resource_zip):
        with zipfile.ZipFile(orphan_resource_zip) as zf:
            manifest = parse_manifest(zf.read("imsmanifest.xml"))
            results = run_resource_checks(manifest, zf)
        warnings = [r for r in results if r.severity == "warning" and not r.passed]
        assert any("res-extra" in (r.message or "") for r in warnings)

    # TODO: add edge case tests for backslash-normalized paths
