from scorm_validator.manifest_parser import ManifestParseError, parse_manifest
from scorm_validator.models import ManifestData, ValidationResult


def run_manifest_checks(
    xml_bytes: bytes,
) -> tuple[list[ValidationResult], ManifestData | None]:
    """Validate XML well-formedness and required manifest elements.

    Returns check results and the parsed ManifestData (None if parsing failed).
    """
    results = []

    # 1. XML well-formedness
    try:
        manifest = parse_manifest(xml_bytes)
    except ManifestParseError as exc:
        results.append(ValidationResult(
            check_name="manifest.well_formed",
            passed=False,
            message=str(exc),
        ))
        return results, None

    results.append(ValidationResult(
        check_name="manifest.well_formed",
        passed=True,
    ))

    # 2. Root element namespace (already validated by parser, but we confirm version detected)
    has_version = manifest.version is not None
    results.append(ValidationResult(
        check_name="manifest.root_namespace",
        passed=True,
        message=f"Detected SCORM {manifest.version.value}" if has_version else None,
    ))

    # 3. Metadata with schema + schemaversion
    has_version_check = manifest.version is not None
    results.append(ValidationResult(
        check_name="manifest.metadata_schema",
        passed=has_version_check,
        message=None if has_version_check else "Missing <schema> or <schemaversion> in metadata",
    ))

    # 4. Organizations section
    has_orgs = len(manifest.organizations) > 0
    results.append(ValidationResult(
        check_name="manifest.has_organizations",
        passed=has_orgs,
        message=None if has_orgs else "No <organization> elements found",
    ))

    # 5. Default org attribute
    if has_orgs:
        org_ids = {org.identifier for org in manifest.organizations}
        default_valid = manifest.default_org in org_ids
        results.append(ValidationResult(
            check_name="manifest.default_org_valid",
            passed=default_valid,
            message=(
                None if default_valid
                else f"default attribute '{manifest.default_org}' doesn't match any organization"
            ),
        ))

    # 6. Each org has a title
    for org in manifest.organizations:
        has_title = bool(org.title)
        results.append(ValidationResult(
            check_name=f"manifest.org_title.{org.identifier}",
            passed=has_title,
            message=None if has_title else f"Organization '{org.identifier}' has no title",
        ))

    # 7. Resources section exists
    has_resources = len(manifest.resources) > 0
    results.append(ValidationResult(
        check_name="manifest.has_resources",
        passed=has_resources,
        message=None if has_resources else "No <resource> elements found",
    ))

    return results, manifest
