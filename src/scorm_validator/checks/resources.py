import zipfile

from scorm_validator.models import ManifestData, ValidationResult


def run_resource_checks(
    manifest: ManifestData, zf: zipfile.ZipFile
) -> list[ValidationResult]:
    results = []
    zip_entries = set(zf.namelist())
    resource_map = {r.identifier: r for r in manifest.resources}

    # collect all identifierrefs from items across all orgs
    referenced_ids = set()
    for org in manifest.organizations:
        _collect_refs(org.items, referenced_ids)

    # 1. Every item identifierref maps to an existing resource
    for org in manifest.organizations:
        _check_item_refs(org.items, resource_map, results)

    # 2. Every resource has type and href
    for res in manifest.resources:
        has_type = bool(res.type)
        has_href = res.href is not None
        if not has_type or not has_href:
            missing = []
            if not has_type:
                missing.append("type")
            if not has_href:
                missing.append("href")
            results.append(ValidationResult(
                check_name=f"resources.attributes.{res.identifier}",
                passed=False,
                message=f"Resource '{res.identifier}' missing: {', '.join(missing)}",
            ))

    # 3. Every file ref exists in the zip
    files_referenced = 0
    files_found = 0
    for res in manifest.resources:
        for fref in res.files:
            files_referenced += 1
            # FIXME: some packages use backslashes in href — normalize to forward slash
            normalized = fref.href.replace("\\", "/")
            if normalized in zip_entries:
                files_found += 1
                fref.exists_in_package = True
            else:
                fref.exists_in_package = False
                results.append(ValidationResult(
                    check_name=f"resources.file_exists.{fref.href}",
                    passed=False,
                    message=(
                        f"File '{fref.href}' referenced in resource "
                        f"'{res.identifier}' not found in package"
                    ),
                ))

    # also check resource href itself (the launch file)
    for res in manifest.resources:
        if res.href and res.href.replace("\\", "/") not in zip_entries:
            results.append(ValidationResult(
                check_name=f"resources.href_exists.{res.identifier}",
                passed=False,
                message=f"Resource '{res.identifier}' href '{res.href}' not found in package",
            ))

    # 4. Orphan resources (not referenced by any item) — warning only
    for res in manifest.resources:
        if res.identifier not in referenced_ids:
            results.append(ValidationResult(
                check_name="resources.orphan",
                passed=False,
                severity="warning",
                message=f"Orphan resource '{res.identifier}' not referenced by any item",
            ))

    return results


def _collect_refs(items, referenced_ids: set):
    for item in items:
        if item.identifierref:
            referenced_ids.add(item.identifierref)
        _collect_refs(item.children, referenced_ids)


def _check_item_refs(items, resource_map: dict, results: list[ValidationResult]):
    for item in items:
        if item.identifierref:
            found = item.identifierref in resource_map
            if not found:
                results.append(ValidationResult(
                    check_name=f"resources.item_ref.{item.identifier}",
                    passed=False,
                    message=(
                        f"Item '{item.identifier}' references resource "
                        f"'{item.identifierref}' which doesn't exist"
                    ),
                ))
        _check_item_refs(item.children, resource_map, results)
