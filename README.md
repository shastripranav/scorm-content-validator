# scorm-validate

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

## Sample Output

```
SCORM Package Validation: course_package.zip
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Version:  SCORM 1.2
  Title:    Introduction to Python
  SCOs:     3 content objects
  Files:    5 referenced, 5 found

  ✅ Structure ........... 4/4 checks passed
  ✅ Manifest ............ 7/7 checks passed
  ✅ SCOs ................ 5/5 checks passed
  ⚠️  Metadata ............ 2/3 checks passed
     └─ WARNING: No description in metadata

  Result: VALID (1 warning)
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
