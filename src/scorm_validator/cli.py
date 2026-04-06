import json
import sys
from pathlib import Path

import click
from rich.console import Console

from scorm_validator.fixers import fix_package
from scorm_validator.models import PackageReport
from scorm_validator.validator import validate_package

console = Console()


@click.command()
@click.argument("packages", nargs=-1, type=click.Path(exists=True))
@click.option("--format", "output_format", type=click.Choice(["text", "json"]), default="text")
@click.option("--verbose", "-v", is_flag=True, help="Show all checks, not just failures")
@click.option("--fix", "apply_fix", is_flag=True, help="Auto-fix common issues")
@click.option("--output", "-o", type=click.Path(), help="Output path for fixed package")
def cli(packages, output_format, verbose, apply_fix, output):
    """Validate SCORM 1.2 and 2004 e-learning packages."""
    if not packages:
        click.echo(click.get_current_context().get_help())
        return

    exit_code = 0
    for pkg in packages:
        if apply_fix:
            out_path = output or _default_fix_path(pkg)
            _handle_fix(pkg, out_path)
            continue

        report = validate_package(pkg)
        if output_format == "json":
            _print_json(report)
        else:
            _print_report(report, verbose)

        if not report.valid:
            exit_code = 1

    sys.exit(exit_code)


def _handle_fix(package_path: str, output_path: str):
    try:
        fixes = fix_package(package_path, output_path)
        if fixes:
            console.print(f"\n[bold green]Fixed:[/] {package_path} → {output_path}")
            for fix in fixes:
                console.print(f"  [dim]•[/] {fix}")
        else:
            console.print(f"\n[bold]No fixes needed:[/] {package_path}")

        # re-validate the fixed package
        report = validate_package(output_path)
        _print_report(report, verbose=False)
    except ValueError as exc:
        console.print(f"\n[bold red]Error:[/] {exc}")
        sys.exit(1)


def _default_fix_path(pkg_path: str) -> str:
    p = Path(pkg_path)
    return str(p.parent / f"{p.stem}_fixed{p.suffix}")


def _print_json(report: PackageReport):
    click.echo(json.dumps(report.to_summary_dict(), indent=2))


def _print_report(report: PackageReport, verbose: bool):
    console.print()
    console.print(f"[bold]SCORM Package Validation:[/] {report.package_path}")
    console.print("━" * 50)

    if report.scorm_version:
        console.print(f"  Version:  SCORM {report.scorm_version.value}")
    if report.title:
        console.print(f"  Title:    {report.title}")
    console.print(f"  SCOs:     {report.sco_count} content objects")
    console.print(
        f"  Files:    {report.files_referenced} referenced, {report.files_found} found"
    )
    console.print()

    # group results by category
    categories = _group_results(report)
    for cat_name, results in categories.items():
        total = len(results)
        passed = sum(1 for r in results if r.passed)
        failed = [r for r in results if not r.passed]

        if not failed:
            dots = "." * (20 - len(cat_name))
            console.print(f"  [green]✅ {cat_name}[/] {dots} {passed}/{total} checks passed")
        else:
            has_errors = any(r.severity == "error" for r in failed)
            icon = "[red]❌[/]" if has_errors else "[yellow]⚠️ [/]"
            dots = "." * (20 - len(cat_name))
            console.print(f"  {icon} {cat_name} {dots} {passed}/{total} checks passed")
            for r in failed:
                prefix = "[red]ERROR[/]" if r.severity == "error" else "[yellow]WARNING[/]"
                console.print(f"     └─ {prefix}: {r.message}")

        if verbose:
            for r in results:
                if r.passed:
                    console.print(f"     [dim]✓ {r.check_name}[/]")

    console.print()
    errors = report.errors
    warnings = report.warnings
    if report.valid:
        parts = ["[bold green]Result: VALID[/]"]
        if warnings:
            parts.append(f"({len(warnings)} warning{'s' if len(warnings) > 1 else ''})")
        console.print("  " + " ".join(parts))
    else:
        console.print(
            f"  [bold red]Result: INVALID[/] "
            f"({len(errors)} error{'s' if len(errors) > 1 else ''}, "
            f"{len(warnings)} warning{'s' if len(warnings) > 1 else ''})"
        )
    console.print()


def _group_results(report: PackageReport) -> dict:
    """Group validation results into display categories."""
    groups: dict[str, list] = {}
    for r in report.results:
        cat = r.check_name.split(".")[0].capitalize()
        # normalize category names
        cat_map = {
            "Structure": "Structure",
            "Manifest": "Manifest",
            "Resources": "Resources",
            "Sco": "SCOs",
            "Metadata": "Metadata",
        }
        display_name = cat_map.get(cat, cat)
        groups.setdefault(display_name, []).append(r)
    return groups
