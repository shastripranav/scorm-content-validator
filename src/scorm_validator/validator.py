"""Orchestrates all validation checks and produces a PackageReport."""

from scorm_validator.checks.manifest import run_manifest_checks
from scorm_validator.checks.metadata import run_metadata_checks
from scorm_validator.checks.resources import run_resource_checks
from scorm_validator.checks.sco import run_sco_checks
from scorm_validator.checks.structure import run_structure_checks
from scorm_validator.models import PackageReport


def validate_package(package_path: str) -> PackageReport:
    """Run all validation checks on a SCORM package and return a full report."""
    all_results = []

    # --- structure checks (zip validity, manifest exists, etc.) ---
    structure_results, zf = run_structure_checks(package_path)
    all_results.extend(structure_results)

    if zf is None:
        return PackageReport(
            package_path=package_path,
            valid=False,
            results=all_results,
        )

    try:
        xml_bytes = zf.read("imsmanifest.xml")

        # --- manifest checks (XML parsing, required elements) ---
        manifest_results, manifest = run_manifest_checks(xml_bytes)
        all_results.extend(manifest_results)

        if manifest is None:
            return PackageReport(
                package_path=package_path,
                valid=False,
                results=all_results,
            )

        # --- resource checks ---
        resource_results = run_resource_checks(manifest, zf)
        all_results.extend(resource_results)

        # count file stats from manifest data
        files_referenced = sum(len(r.files) for r in manifest.resources)
        files_found = sum(
            1 for r in manifest.resources for f in r.files if f.exists_in_package
        )

        # --- sco checks ---
        sco_results = run_sco_checks(manifest, zf)
        all_results.extend(sco_results)

        sco_count = sum(
            1 for r in manifest.resources
            if r.scorm_type and r.scorm_type.lower() == "sco"
        )

        # --- metadata checks ---
        metadata_results = run_metadata_checks(manifest)
        all_results.extend(metadata_results)

        # a package is valid if no error-severity checks failed
        has_errors = any(
            not r.passed and r.severity == "error" for r in all_results
        )

        return PackageReport(
            package_path=package_path,
            scorm_version=manifest.version,
            title=manifest.title,
            valid=not has_errors,
            results=all_results,
            sco_count=sco_count,
            resource_count=len(manifest.resources),
            files_referenced=files_referenced,
            files_found=files_found,
        )
    finally:
        zf.close()
