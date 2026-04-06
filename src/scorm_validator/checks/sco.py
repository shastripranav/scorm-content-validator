import zipfile

from scorm_validator.models import ManifestData, ValidationResult


def run_sco_checks(
    manifest: ManifestData, zf: zipfile.ZipFile
) -> list[ValidationResult]:
    results = []
    zip_entries = set(zf.namelist())

    scos = [r for r in manifest.resources if r.scorm_type and r.scorm_type.lower() == "sco"]

    # 1. At least one SCO
    results.append(ValidationResult(
        check_name="sco.has_scos",
        passed=len(scos) > 0,
        message=None if scos else "No SCO resources found in package",
    ))

    # 2. Each SCO has a valid launch URL
    for sco in scos:
        if not sco.href:
            results.append(ValidationResult(
                check_name=f"sco.launch_url.{sco.identifier}",
                passed=False,
                message=f"SCO '{sco.identifier}' has no launch URL (missing href)",
            ))
        else:
            normalized = sco.href.replace("\\", "/")
            exists = normalized in zip_entries
            results.append(ValidationResult(
                check_name=f"sco.launch_url.{sco.identifier}",
                passed=exists,
                message=(
                    None if exists
                    else f"SCO '{sco.identifier}' launch URL '{sco.href}' not found in package"
                ),
            ))

    # 3. SCO identifiers are unique
    sco_ids = [s.identifier for s in scos]
    seen = set()
    dupes = set()
    for sid in sco_ids:
        if sid in seen:
            dupes.add(sid)
        seen.add(sid)

    results.append(ValidationResult(
        check_name="sco.unique_identifiers",
        passed=len(dupes) == 0,
        message=(
            None if not dupes
            else f"Duplicate SCO identifiers: {', '.join(sorted(dupes))}"
        ),
    ))

    return results
