# scorm-validate

[![CI](https://github.com/shastripranav/scorm-content-validator/actions/workflows/ci.yml/badge.svg)](https://github.com/shastripranav/scorm-content-validator/actions/workflows/ci.yml)

CLI tool for validating SCORM 1.2 and SCORM 2004 e-learning packages before uploading to an LMS.

SCORM packages frequently fail when uploaded to Learning Management Systems due to malformed manifests, missing files, or invalid metadata. This tool catches those issues early so you can fix them before deployment.

## Install

```bash
pip install -e ".[dev]"
```

## Usage

```bash
# Validate a package
scorm-validate package.zip

# JSON output (for CI/CD pipelines)
scorm-validate package.zip --format json

# Show all checks, not just failures
scorm-validate package.zip --verbose

# Auto-fix common issues
scorm-validate package.zip --fix --output fixed_package.zip

# Validate multiple packages
scorm-validate *.zip
```

## Example Output

A valid SCORM 1.2 package:

```
$ scorm-validate tests/fixtures/valid_scorm12.zip

SCORM Package Validation: tests/fixtures/valid_scorm12.zip
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Version:  SCORM 1.2
  Title:    Test Course 1.2
  SCOs:     2 content objects
  Files:    3 referenced, 3 found

  ✅ Structure ........... 4/4 checks passed
  ✅ Manifest ............ 7/7 checks passed
  ✅ SCOs ................ 4/4 checks passed
  ✅ Metadata ............ 3/3 checks passed

  Result: VALID
```

A package whose manifest references files that aren't in the zip:

```
$ scorm-validate tests/fixtures/missing_files.zip

SCORM Package Validation: tests/fixtures/missing_files.zip
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Version:  SCORM 1.2
  Title:    Test Course 1.2
  SCOs:     2 content objects
  Files:    3 referenced, 0 found

  ✅ Structure ........... 4/4 checks passed
  ✅ Manifest ............ 7/7 checks passed
  ❌ Resources ........... 0/5 checks passed
     └─ ERROR: File 'module1/index.html' referenced in resource 'res-1' not found in package
     └─ ERROR: File 'module1/style.css' referenced in resource 'res-1' not found in package
     └─ ERROR: File 'module2/index.html' referenced in resource 'res-2' not found in package
     └─ ERROR: Resource 'res-1' href 'module1/index.html' not found in package
     └─ ERROR: Resource 'res-2' href 'module2/index.html' not found in package
  ❌ SCOs ................ 2/4 checks passed
     └─ ERROR: SCO 'res-1' launch URL 'module1/index.html' not found in package
     └─ ERROR: SCO 'res-2' launch URL 'module2/index.html' not found in package
  ✅ Metadata ............ 3/3 checks passed

  Result: INVALID (7 errors, 0 warning)
```

## What Gets Validated

| Category   | Checks |
|-----------|--------|
| Structure | Valid zip, manifest exists, no path traversal, size limits |
| Manifest  | XML well-formed, correct namespace, required sections, org structure |
| Resources | Item refs resolve, file refs exist in package, orphan detection |
| SCOs      | At least one SCO, valid launch URLs, unique identifiers |
| Metadata  | Title present, description, manifest identifier |

## Auto-Fix

The `--fix` flag repairs common issues:

- Strips UTF-8 BOM from manifest
- Fixes encoding declaration mismatches
- Inserts missing `<metadata>` section
- Adds empty `<description>` element

## Architecture

```
src/scorm_validator/
├── cli.py              # Click CLI entry point
├── validator.py        # Orchestrates all checks
├── manifest_parser.py  # XML → ManifestData (handles 1.2 + 2004 namespaces)
├── models.py           # Pydantic models (ManifestData, PackageReport)
├── fixers.py           # Auto-fix logic
└── checks/
    ├── structure.py    # Zip structure validation
    ├── manifest.py     # XML + manifest element checks
    ├── resources.py    # File reference validation
    ├── sco.py          # SCO-specific checks
    └── metadata.py     # Metadata completeness
```

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest -v

# Run linter
ruff check src/ tests/

# Run with coverage
pytest --cov=scorm_validator --cov-report=term-missing
```

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `SCORM_MAX_SIZE`    | 2GB     | Max uncompressed package size |
| `LOG_LEVEL`         | WARNING | Logging verbosity |

## License

MIT
