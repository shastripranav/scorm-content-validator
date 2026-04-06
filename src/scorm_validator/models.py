from enum import Enum

from pydantic import BaseModel


class SCORMVersion(str, Enum):
    V12 = "1.2"
    V2004_3RD = "2004 3rd Edition"
    V2004_4TH = "2004 4th Edition"


class FileRef(BaseModel):
    href: str
    exists_in_package: bool = True


class Resource(BaseModel):
    identifier: str
    type: str
    href: str | None = None
    scorm_type: str | None = None
    files: list[FileRef] = []


class Item(BaseModel):
    identifier: str
    title: str
    identifierref: str | None = None
    children: list["Item"] = []


class Organization(BaseModel):
    identifier: str
    title: str
    items: list[Item] = []


class ManifestData(BaseModel):
    """Structured representation of imsmanifest.xml contents.

    Handles both SCORM 1.2 and 2004 manifests — the parser normalizes
    namespace differences before populating this model.
    """

    identifier: str | None = None
    version: SCORMVersion | None = None
    title: str | None = None
    description: str | None = None
    organizations: list[Organization] = []
    resources: list[Resource] = []
    default_org: str | None = None


class ValidationResult(BaseModel):
    check_name: str
    passed: bool
    severity: str = "error"
    message: str | None = None


class PackageReport(BaseModel):
    """Final validation report for a SCORM package."""

    package_path: str
    scorm_version: SCORMVersion | None = None
    title: str | None = None
    valid: bool
    results: list[ValidationResult] = []
    sco_count: int = 0
    resource_count: int = 0
    files_referenced: int = 0
    files_found: int = 0

    @property
    def errors(self) -> list[ValidationResult]:
        return [r for r in self.results if not r.passed and r.severity == "error"]

    @property
    def warnings(self) -> list[ValidationResult]:
        return [r for r in self.results if not r.passed and r.severity == "warning"]

    def to_summary_dict(self) -> dict:
        return {
            "package": self.package_path,
            "scorm_version": self.scorm_version.value if self.scorm_version else None,
            "title": self.title,
            "valid": self.valid,
            "errors": [
                {"check": e.check_name, "message": e.message} for e in self.errors
            ],
            "warnings": [
                {"check": w.check_name, "message": w.message} for w in self.warnings
            ],
            "summary": {
                "scos": self.sco_count,
                "resources": self.resource_count,
                "files_referenced": self.files_referenced,
                "files_found": self.files_found,
            },
        }


# SCORM namespace map — the main difference between 1.2 and 2004
NAMESPACES = {
    "imscp12": "http://www.imsproject.org/xsd/imscp_rootv1p1p2",
    "imscp2004": "http://www.imsglobal.org/xsd/imscp_v1p1",
    "adlcp12": "http://www.adlnet.org/xsd/adlcp_rootv1p2",
    "adlcp2004": "http://www.adlnet.org/xsd/adlcp_v1p3",
    "imsss": "http://www.imsglobal.org/xsd/imsss",
    "adlseq": "http://www.adlnet.org/xsd/adlseq_v1p3",
    "adlnav": "http://www.adlnet.org/xsd/adlnav_v1p3",
}

# reverse lookup: namespace URI -> version family
NS_TO_VERSION = {
    NAMESPACES["imscp12"]: "1.2",
    NAMESPACES["imscp2004"]: "2004",
}

# schemaversion string -> SCORMVersion enum
SCHEMA_VERSION_MAP: dict[str, SCORMVersion] = {
    "1.2": SCORMVersion.V12,
    "2004 3rd edition": SCORMVersion.V2004_3RD,
    "2004 4th edition": SCORMVersion.V2004_4TH,
    # some packages use inconsistent casing
    "2004 3rd Edition": SCORMVersion.V2004_3RD,
    "2004 4th Edition": SCORMVersion.V2004_4TH,
}
