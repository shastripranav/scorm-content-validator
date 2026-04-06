import os

from scorm_validator.checks.structure import run_structure_checks


class TestStructureChecks:
    def test_valid_package(self, valid_scorm12_zip):
        results, zf = run_structure_checks(valid_scorm12_zip)
        assert zf is not None
        zf.close()
        assert all(r.passed for r in results)

    def test_file_not_found(self):
        results, zf = run_structure_checks("/nonexistent/path.zip")
        assert zf is None
        assert any("not found" in (r.message or "") for r in results)

    def test_not_a_zip(self, tmp_dir):
        fake = os.path.join(tmp_dir, "fake.zip")
        with open(fake, "w") as f:
            f.write("this is not a zip file")
        results, zf = run_structure_checks(fake)
        assert zf is None
        assert not results[0].passed

    def test_missing_manifest(self, missing_manifest_zip):
        results, zf = run_structure_checks(missing_manifest_zip)
        assert zf is None
        manifest_check = next(
            r for r in results if r.check_name == "structure.manifest_exists"
        )
        assert not manifest_check.passed

    def test_no_path_traversal(self, valid_scorm12_zip):
        results, zf = run_structure_checks(valid_scorm12_zip)
        if zf:
            zf.close()
        traversal = next(
            r for r in results if r.check_name == "structure.no_path_traversal"
        )
        assert traversal.passed
