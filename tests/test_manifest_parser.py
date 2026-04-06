import pytest
from conftest import SCORM12_MANIFEST, SCORM2004_MANIFEST

from scorm_validator.manifest_parser import ManifestParseError, parse_manifest
from scorm_validator.models import SCORMVersion


class TestManifestParser:
    def test_parse_scorm12(self):
        manifest = parse_manifest(SCORM12_MANIFEST.encode())
        assert manifest.version == SCORMVersion.V12
        assert manifest.identifier == "test-course-12"
        assert len(manifest.organizations) == 1
        assert len(manifest.resources) == 2
        assert manifest.title == "Test Course 1.2"

    def test_parse_scorm2004(self):
        manifest = parse_manifest(SCORM2004_MANIFEST.encode())
        assert manifest.version == SCORMVersion.V2004_4TH
        assert manifest.identifier == "test-course-2004"
        assert len(manifest.resources) == 1
        # 2004 uses camelCase scormType
        assert manifest.resources[0].scorm_type == "sco"

    def test_parse_items_nested(self):
        manifest = parse_manifest(SCORM12_MANIFEST.encode())
        org = manifest.organizations[0]
        assert len(org.items) == 2
        assert org.items[0].identifier == "item-1"
        assert org.items[0].identifierref == "res-1"
        assert org.items[1].title == "Module 2"

    def test_parse_resources_files(self):
        manifest = parse_manifest(SCORM12_MANIFEST.encode())
        res1 = manifest.resources[0]
        assert res1.href == "module1/index.html"
        assert len(res1.files) == 2
        assert res1.files[0].href == "module1/index.html"

    def test_malformed_xml_raises(self):
        with pytest.raises(ManifestParseError, match="Malformed XML"):
            parse_manifest(b"<manifest><broken>")

    def test_unrecognized_namespace_raises(self):
        xml = b'<manifest xmlns="http://example.com/fake"></manifest>'
        with pytest.raises(ManifestParseError, match="not a recognized SCORM"):
            parse_manifest(xml)

    def test_bom_stripped(self):
        bom_xml = b"\xef\xbb\xbf" + SCORM12_MANIFEST.encode()
        manifest = parse_manifest(bom_xml)
        assert manifest.version == SCORMVersion.V12

    def test_description_parsed(self):
        manifest = parse_manifest(SCORM12_MANIFEST.encode())
        assert manifest.description == "A test SCORM 1.2 package"

    def test_default_org(self):
        manifest = parse_manifest(SCORM12_MANIFEST.encode())
        assert manifest.default_org == "org-1"
