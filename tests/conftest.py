"""Shared test fixtures — creates SCORM packages programmatically."""

import os
import tempfile
import zipfile

import pytest

SCORM12_MANIFEST = """\
<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="test-course-12" version="1.0"
          xmlns="http://www.imsproject.org/xsd/imscp_rootv1p1p2"
          xmlns:adlcp="http://www.adlnet.org/xsd/adlcp_rootv1p2">
  <metadata>
    <schema>ADL SCORM</schema>
    <schemaversion>1.2</schemaversion>
    <description>A test SCORM 1.2 package</description>
  </metadata>
  <organizations default="org-1">
    <organization identifier="org-1">
      <title>Test Course 1.2</title>
      <item identifier="item-1" identifierref="res-1">
        <title>Module 1</title>
      </item>
      <item identifier="item-2" identifierref="res-2">
        <title>Module 2</title>
      </item>
    </organization>
  </organizations>
  <resources>
    <resource identifier="res-1" type="webcontent" adlcp:scormtype="sco" href="module1/index.html">
      <file href="module1/index.html"/>
      <file href="module1/style.css"/>
    </resource>
    <resource identifier="res-2" type="webcontent" adlcp:scormtype="sco" href="module2/index.html">
      <file href="module2/index.html"/>
    </resource>
  </resources>
</manifest>"""


SCORM2004_MANIFEST = """\
<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="test-course-2004" version="1.0"
          xmlns="http://www.imsglobal.org/xsd/imscp_v1p1"
          xmlns:adlcp="http://www.adlnet.org/xsd/adlcp_v1p3">
  <metadata>
    <schema>ADL SCORM</schema>
    <schemaversion>2004 4th Edition</schemaversion>
    <description>A test SCORM 2004 package</description>
  </metadata>
  <organizations default="org-1">
    <organization identifier="org-1">
      <title>Test Course 2004</title>
      <item identifier="item-1" identifierref="res-1">
        <title>Lesson 1</title>
      </item>
    </organization>
  </organizations>
  <resources>
    <resource identifier="res-1" type="webcontent" adlcp:scormType="sco" href="lesson1/index.html">
      <file href="lesson1/index.html"/>
    </resource>
  </resources>
</manifest>"""

CONTENT_FILES = {
    "module1/index.html": "<html><body><h1>Module 1</h1></body></html>",
    "module1/style.css": "body { margin: 0; }",
    "module2/index.html": "<html><body><h1>Module 2</h1></body></html>",
}

CONTENT_FILES_2004 = {
    "lesson1/index.html": "<html><body><h1>Lesson 1</h1></body></html>",
}


def _build_scorm_zip(manifest_xml: str, content_files: dict, tmpdir: str, name: str) -> str:
    pkg_path = os.path.join(tmpdir, name)
    with zipfile.ZipFile(pkg_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("imsmanifest.xml", manifest_xml)
        for path, content in content_files.items():
            zf.writestr(path, content)
    return pkg_path


@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture
def valid_scorm12_zip(tmp_dir):
    return _build_scorm_zip(SCORM12_MANIFEST, CONTENT_FILES, tmp_dir, "valid_scorm12.zip")


@pytest.fixture
def valid_scorm2004_zip(tmp_dir):
    return _build_scorm_zip(
        SCORM2004_MANIFEST, CONTENT_FILES_2004, tmp_dir, "valid_scorm2004.zip"
    )


@pytest.fixture
def missing_manifest_zip(tmp_dir):
    """Package with content but no imsmanifest.xml."""
    pkg_path = os.path.join(tmp_dir, "missing_manifest.zip")
    with zipfile.ZipFile(pkg_path, "w") as zf:
        zf.writestr("content/index.html", "<html><body>No manifest</body></html>")
    return pkg_path


@pytest.fixture
def missing_files_zip(tmp_dir):
    """Manifest references files that don't exist in the zip."""
    return _build_scorm_zip(SCORM12_MANIFEST, {}, tmp_dir, "missing_files.zip")


@pytest.fixture
def malformed_xml_zip(tmp_dir):
    pkg_path = os.path.join(tmp_dir, "malformed_xml.zip")
    with zipfile.ZipFile(pkg_path, "w") as zf:
        zf.writestr("imsmanifest.xml", "<manifest><broken>no closing tag")
    return pkg_path


@pytest.fixture
def no_sco_zip(tmp_dir):
    """Package with resources but none marked as SCO."""
    manifest = SCORM12_MANIFEST.replace('adlcp:scormtype="sco"', 'adlcp:scormtype="asset"')
    return _build_scorm_zip(manifest, CONTENT_FILES, tmp_dir, "no_sco.zip")


@pytest.fixture
def bom_manifest_zip(tmp_dir):
    """Package with UTF-8 BOM in manifest."""
    bom_manifest = b"\xef\xbb\xbf" + SCORM12_MANIFEST.encode("utf-8")
    pkg_path = os.path.join(tmp_dir, "bom_manifest.zip")
    with zipfile.ZipFile(pkg_path, "w") as zf:
        zf.writestr("imsmanifest.xml", bom_manifest)
        for path, content in CONTENT_FILES.items():
            zf.writestr(path, content)
    return pkg_path


@pytest.fixture
def no_metadata_zip(tmp_dir):
    """Package without metadata section."""
    manifest = """\
<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="no-meta"
          xmlns="http://www.imsproject.org/xsd/imscp_rootv1p1p2"
          xmlns:adlcp="http://www.adlnet.org/xsd/adlcp_rootv1p2">
  <organizations default="org-1">
    <organization identifier="org-1">
      <title>No Metadata Course</title>
      <item identifier="item-1" identifierref="res-1">
        <title>Module 1</title>
      </item>
    </organization>
  </organizations>
  <resources>
    <resource identifier="res-1" type="webcontent" adlcp:scormtype="sco" href="module1/index.html">
      <file href="module1/index.html"/>
    </resource>
  </resources>
</manifest>"""
    return _build_scorm_zip(manifest, CONTENT_FILES, tmp_dir, "no_metadata.zip")


@pytest.fixture
def orphan_resource_zip(tmp_dir):
    """Package with a resource not referenced by any item."""
    manifest = """\
<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="orphan-test"
          xmlns="http://www.imsproject.org/xsd/imscp_rootv1p1p2"
          xmlns:adlcp="http://www.adlnet.org/xsd/adlcp_rootv1p2">
  <metadata>
    <schema>ADL SCORM</schema>
    <schemaversion>1.2</schemaversion>
  </metadata>
  <organizations default="org-1">
    <organization identifier="org-1">
      <title>Orphan Test</title>
      <item identifier="item-1" identifierref="res-1">
        <title>Module 1</title>
      </item>
    </organization>
  </organizations>
  <resources>
    <resource identifier="res-1" type="webcontent" adlcp:scormtype="sco" href="module1/index.html">
      <file href="module1/index.html"/>
    </resource>
    <resource identifier="res-extra" type="webcontent"
              adlcp:scormtype="asset" href="extra/bonus.html">
      <file href="extra/bonus.html"/>
    </resource>
  </resources>
</manifest>"""
    files = {
        "module1/index.html": "<html><body>Module 1</body></html>",
        "extra/bonus.html": "<html><body>Bonus</body></html>",
    }
    return _build_scorm_zip(manifest, files, tmp_dir, "orphan_resource.zip")
