from scorm_validator.models import ManifestData, ValidationResult


def run_metadata_checks(manifest: ManifestData) -> list[ValidationResult]:
    results = []

    # 1. Course title present and non-empty
    has_title = bool(manifest.title)
    results.append(ValidationResult(
        check_name="metadata.title",
        passed=has_title,
        message=None if has_title else "Course title is missing or empty",
    ))

    # 2. Description present (warning if missing)
    has_desc = bool(manifest.description)
    results.append(ValidationResult(
        check_name="metadata.description",
        passed=has_desc,
        severity="warning",
        message=None if has_desc else "No description in metadata",
    ))

    # 3. Manifest identifier attribute
    has_id = bool(manifest.identifier)
    results.append(ValidationResult(
        check_name="metadata.identifier",
        passed=has_id,
        severity="warning",
        message=None if has_id else "Manifest element has no identifier attribute",
    ))

    return results
