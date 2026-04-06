import zipfile
from pathlib import Path

from scorm_validator.models import ValidationResult

MAX_UNCOMPRESSED_SIZE = 2 * 1024 * 1024 * 1024  # 2GB


def run_structure_checks(
    package_path: str,
) -> tuple[list[ValidationResult], zipfile.ZipFile | None]:
    """Validate zip structure and return an open ZipFile handle if valid.

    Returns results and the ZipFile for downstream checks to use.
    The caller is responsible for closing the zipfile.
    """
    results = []
    zf = None

    # 1. Valid zip file
    path = Path(package_path)
    if not path.exists():
        results.append(ValidationResult(
            check_name="structure.file_exists",
            passed=False,
            message=f"File not found: {package_path}",
        ))
        return results, None

    if not zipfile.is_zipfile(path):
        results.append(ValidationResult(
            check_name="structure.valid_zip",
            passed=False,
            message="File is not a valid zip archive",
        ))
        return results, None

    try:
        zf = zipfile.ZipFile(path, "r")
    except (zipfile.BadZipFile, OSError) as exc:
        results.append(ValidationResult(
            check_name="structure.valid_zip",
            passed=False,
            message=f"Cannot open zip: {exc}",
        ))
        return results, None

    results.append(ValidationResult(
        check_name="structure.valid_zip",
        passed=True,
    ))

    # 2. imsmanifest.xml at root
    names = zf.namelist()
    has_manifest = "imsmanifest.xml" in names
    results.append(ValidationResult(
        check_name="structure.manifest_exists",
        passed=has_manifest,
        message=None if has_manifest else "imsmanifest.xml not found at package root",
    ))

    # 3. Path traversal check
    traversal_entries = [n for n in names if ".." in n.split("/")]
    has_traversal = len(traversal_entries) > 0
    results.append(ValidationResult(
        check_name="structure.no_path_traversal",
        passed=not has_traversal,
        message=(
            f"Dangerous path traversal in zip entries: {traversal_entries[:3]}"
            if has_traversal
            else None
        ),
    ))

    # 4. Total uncompressed size
    total_size = sum(info.file_size for info in zf.infolist())
    too_large = total_size > MAX_UNCOMPRESSED_SIZE
    results.append(ValidationResult(
        check_name="structure.reasonable_size",
        passed=not too_large,
        severity="warning",
        message=(
            f"Package uncompressed size ({total_size / (1024**3):.1f}GB) exceeds 2GB"
            if too_large
            else None
        ),
    ))

    if not has_manifest:
        zf.close()
        zf = None

    return results, zf
