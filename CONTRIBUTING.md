# Contributing to scorm-content-validator

Thanks for considering a contribution. This project is MIT licensed and contributions of any size are welcome — bug reports, fixes, new SCORM edge cases, and documentation improvements all help.

## How to Contribute

1. Fork the repository on GitHub.
2. Create a topic branch off `main`: `git checkout -b fix/imsmanifest-parser`.
3. Make your changes, add tests, and run the full test suite locally.
4. Open a pull request against `main` with a clear description of what changed and why.

## Development setup

Clone the repo and install in editable mode with the dev extras:

```bash
pip install -e ".[dev]"
```

## Code style

Source code is formatted and linted with [ruff](https://docs.astral.sh/ruff/). Before pushing:

```bash
ruff check src/ tests/
ruff format src/ tests/
```

## Testing

Run the full pytest suite:

```bash
pytest -v
```

Please make sure all tests pass before opening a PR. If you're adding a new feature or fixing a bug, please add a test that covers the change. SCORM edge cases especially benefit from a fixture file under `tests/fixtures/`.

## Questions

Open an issue with the `question` label and I'll get back to you.
