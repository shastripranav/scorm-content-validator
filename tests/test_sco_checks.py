import zipfile

from scorm_validator.checks.sco import run_sco_checks
from scorm_validator.manifest_parser import parse_manifest


class TestSCOChecks:
    def test_valid_scos(self, valid_scorm12_zip):
        with zipfile.ZipFile(valid_scorm12_zip) as zf:
            manifest = parse_manifest(zf.read("imsmanifest.xml"))
            results = run_sco_checks(manifest, zf)
        assert all(r.passed for r in results)

    def test_no_sco_detected(self, no_sco_zip):
        with zipfile.ZipFile(no_sco_zip) as zf:
            manifest = parse_manifest(zf.read("imsmanifest.xml"))
            results = run_sco_checks(manifest, zf)
        sco_check = next(r for r in results if r.check_name == "sco.has_scos")
        assert not sco_check.passed
