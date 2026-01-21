Copilot instructions for living-doc-collector-gh

Purpose
This repo contains a Python GitHub Action that collects “living documentation” data from GitHub (e.g., Projects/Issues) and writes it out in a machine-readable format (JSON) suitable for downstream documentation generation.

Context
- The action is intended to run on GitHub Actions runners.
- Inputs are read from `INPUT_*` environment variables provided by GitHub Actions (see `action.yml`).
- Output is written under the repository’s configured output folder (see code that uses `OUTPUT_PATH`) and exposed via the action output `output-path`.

Coding guidelines
- Keep changes small and focused
- Prefer clear, explicit code over clever tricks
- Do not change existing error messages or log texts without a good reason, because tests check them
- Keep behaviour of action inputs stable unless the contract is intentionally updated

Python and style
- Target Python 3.14 or later (match repo docs/tooling)
- Add type hints for new public functions and classes
- Use logging, not print
- All Python imports must be placed at the top of the file, not inside methods or functions

Testing
- Use pytest with tests located in tests/
- Test behaviour: return values, raised errors, log messages, exit codes
- Mock environment variables; do not call external APIs (GitHub) in unit tests

Tooling
- Format with Black using pyproject.toml
- Run Pylint on tracked Python files, excluding tests/, and aim for score 9.5 or higher
- Run mypy and prefer fixing types instead of ignoring errors
- Use pytest-cov and keep coverage at or above 80 percent

Pre-commit Quality Gates:
Before submitting any PR or claiming work is complete, ALWAYS run these checks locally:

1. Testing
- Run unit tests: `pytest tests/`
- Run integration/verification tests if they exist
- Ensure exit code 0 for all tests
- Fix any test failures before proceeding

2. Code Quality
- Format with Black: `black $(git ls-files '*.py')`
- Run Pylint: `pylint $(git ls-files '*.py')`
  - Target score: ≥ 9.5/10
  - Fix warnings before submitting
- Run mypy: `mypy .` or `mypy <changed_files>`
  - Resolve type errors or use appropriate type ignore comments
  - Document why type ignores are necessary

3. Verification Workflow
3.1. **After writing code**: Run tests immediately
3.2. **After tests pass**: Run linters (Black, Pylint, mypy)
3.3. **After linters pass**: Commit changes
3.4. **Before pushing**: Run full quality gate again

4. Early Detection
- Run quality checks EARLY in development, not at the end
- Fix issues incrementally as they appear
- Don't accumulate technical debt

Common Pitfalls to Avoid:

Dependencies
- Check library compatibility with target Python version BEFORE using
- Test imports locally before committing
- For untyped libraries: add `# type: ignore[import-untyped]` comments

Logging
- Always use lazy % formatting: `logger.info("msg %s", var)`
- NEVER use f-strings in logging: ~~`logger.info(f"msg {var}")`~~
- Reason: avoids string interpolation when logging is disabled

Variable Cleanup
- Remove unused variables promptly
- Run linters to catch them early
- Don't leave dead code

Checklist Template
Use this for every PR:
- All tests pass locally (pytest)
- Black formatting applied
- Pylint score ≥ 9.5
- Mypy passes (or documented type ignores)
- No unused imports/variables
- Logging uses lazy % formatting
- Dependencies tested locally
- Documentation updated

Architecture notes
- Action must work on a GitHub Actions runner with only `requirements.txt` dependencies
- Keep core logic free of I/O where practical; keep environment access at the edges

File overview
- main.py: sets up logging and runs the action (if present)
- action.yml: composite action definition (if present)

Common commands
- Create and activate venv, install deps:
  - python3 -m venv .venv
  -	source .venv/bin/activate
  - pip install -r requirements.txt
- Run tests:
  - pytest tests/
- Run coverage:
  - pytest --ignore=tests/integration --cov=. tests/ --cov-fail-under=80 --cov-report=html
- Format and lint:
  - black
  - pylint $(git ls-files "*.py")
  - mypy .

Learned rules
- Keep error messages stable; tests assert on exact strings
- Do not change exit codes for existing failure scenarios
