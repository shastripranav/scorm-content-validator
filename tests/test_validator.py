from scorm_validator.validator import validate_package


class TestValidator:
    def test_valid_scorm12(self, valid_scorm12_zip):
        report = validate_package(valid_scorm12_zip)
        assert report.valid
        assert report.scorm_version is not None
        assert report.sco_count == 2
        assert report.files_referenced == 3
        assert report.files_found == 3

    def test_valid_scorm2004(self, valid_scorm2004_zip):
        report = validate_package(valid_scorm2004_zip)
        assert report.valid
        assert report.sco_count == 1

    def test_missing_manifest_invalid(self, missing_manifest_zip):
        report = validate_package(missing_manifest_zip)
        assert not report.valid

    def test_malformed_xml_invalid(self, malformed_xml_zip):
        report = validate_package(malformed_xml_zip)
        assert not report.valid

    def test_missing_files_invalid(self, missing_files_zip):
        report = validate_package(missing_files_zip)
        assert not report.valid
        assert len(report.errors) > 0

    def test_report_json_output(self, valid_scorm12_zip):
        report = validate_package(valid_scorm12_zip)
        summary = report.to_summary_dict()
        assert summary["valid"] is True
        assert summary["scorm_version"] == "1.2"
        assert "summary" in summary

    def test_nonexistent_file(self):
        report = validate_package("/does/not/exist.zip")
        assert not report.valid

    def test_orphan_resource_still_valid(self, orphan_resource_zip):
        """Orphan resources produce warnings, not errors — package is still valid."""
        report = validate_package(orphan_resource_zip)
        assert report.valid
        assert len(report.warnings) > 0
