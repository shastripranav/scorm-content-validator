# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-05-08

### Added

- SCORM 1.2 package validation covering zip structure, manifest XML, resource references, SCOs, and metadata
- SCORM 2004 (3rd and 4th editions) package validation with namespace auto-detection
- Auto-fix mode (`--fix` flag) for common manifest issues: strips UTF-8 BOM, fixes encoding declaration mismatches, inserts missing `<metadata>` sections, and adds empty `<description>` elements
- JSON output format (`--format json`) for CI/CD pipeline integration
- Verbose mode (`--verbose` flag) that shows all checks rather than only failures
- Categorized validation report (Structure, Manifest, Resources, SCOs, Metadata) with error and warning severity levels
- Resource validation including item reference resolution, file existence checks, and orphan detection
- SCO checks for valid launch URLs, unique identifiers, and at least one content object
- Path-traversal protection and configurable max-package-size limit (`SCORM_MAX_SIZE`)
- CLI entry point (`scorm-validate`) supporting both single-file and bulk (glob) package validation
- Test fixtures and pytest suite covering valid packages, common errors, and edge cases across both SCORM versions
