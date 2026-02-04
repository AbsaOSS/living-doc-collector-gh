Purpose
- Must follow these instructions when proposing changes for living-doc-collector-gh.
- Must keep repo-specific facts in “Repo additions” (end of file).

Structure
- Must keep sections in the order defined in this file.
- Prefer bullet lists over paragraphs.
- Must write rules as constraints using “Must / Must not / Prefer / Avoid”.
- Must keep wording concrete and reviewable.
- Must keep a single blank line at end of file.

Context
- If this repository is a GitHub Action or CLI:
  - Must assume it runs in an automation runner environment.
  - Must treat environment variables as the primary input channel.
  - Must write outputs only to the configured output folder and expose contract outputs via the declared action/CLI interface.

Coding guidelines
- Must keep changes small and focused.
- Prefer clear, explicit code over clever tricks.
- Must keep externally-visible behavior stable unless intentionally updating the contract.
- Must keep pure logic free of environment access where practical; route I/O and env through dedicated boundaries.

Output discipline
- Prefer concise responses (aim <= 10 lines in the final recap).
- Must not restate large file contents/configs/checklists; link and summarize deltas.
- Prefer actionable bullets over prose.
- When making code changes, must end with:
  - What changed
  - Why
  - How to verify (commands/tests)
- Avoid deep rationale, alternatives, or long examples unless explicitly requested.

PR Body Management
- Must treat the PR description as an append-only changelog.
- Must not rewrite/replace the entire PR body; must append updates.
- Prefer this structure:
  - Keep original description at top.
  - Add updates chronologically below.
  - Use headings like “## Update YYYY-MM-DD” or “## Changes Added”.
  - Each update references the commit hash that introduced the change.

Inputs
- If this repository defines inputs via environment variables:
  - Must treat `INPUT_*` environment variables as the canonical inputs.
  - Must centralize validation in one input/validation layer.
  - Avoid duplicating validation across modules.
- If defaults exist:
  - Must document default behavior in one place.

Language and style
- Must target the runtime/version defined in “Repo additions”.
- Must add type hints/types for new public APIs.
- Must use the project logging framework; must not use `print`.
- Must follow the repo import/include conventions (for Python: imports at top of file).
- Must not disable linter rules inline unless the repo documents an exception process.

String formatting
- Must follow the repo-defined formatting rules in “Repo additions”.
- Logging:
  - Must use the repo's preferred interpolation style (typically lazy/structured).
- Exceptions/errors:
  - Prefer the clearest formatting rule; must keep contract-sensitive strings stable.

Docstrings and comments
- Must match existing module style and keep consistent across the repo.
- Docstrings:
  - Prefer a short summary line.
  - Prefer structured sections (`Parameters:` / `Returns:`) when useful.
  - Avoid tutorials/long prose.
- Comments:
  - Prefer self-explanatory code.
  - Comment only for intent/edge cases (the “why”).
  - Avoid blocks that restate what code already says.

Patterns
- Error handling:
  - Prefer leaf modules raise exceptions.
  - Prefer entry points translate failures into exit codes / action-failure output.
- Constructors (if applicable):
  - Prefer constructors do not throw; validate via factory/validator if needed.
- Internal helpers:
  - Prefer private helpers for internal behavior (`_name` in Python).
- Testability:
  - Must keep integration boundaries explicit and mockable.
  - Must not make real network calls in unit tests.

Testing
- Must use pytest for unit tests.
- Must keep tests under `tests/`.
- Must test behavior via return values, raised errors, log messages, and exit codes.
- Must mock environment variables; must not call external services (e.g., GitHub APIs) in unit tests.
- Prefer shared fixtures in `conftest.py`.

Tooling
- Must keep tooling rules aligned with repo config files (e.g., `pyproject.toml`).
- Formatting:
  - Must use Black.
- Linting:
  - Must use Pylint and address warnings.
- Type checking:
  - Must run mypy and prefer fixing types over ignoring errors.
- Coverage:
  - Must use pytest-cov and meet the coverage minimum defined in “Repo additions”.

Quality gates
- Must run after changes; fix issues if below threshold:
  - Tests: `pytest tests/`
  - Format: `black $(git ls-files '*.py')`
  - Lint: `pylint $(git ls-files '*.py' ':!:tests/**')`
  - Types: `mypy .`
- If the repo defines special lint scopes (e.g., exclude `tests/`), must use the repo's canonical commands from “Repo additions”.

Common pitfalls to avoid
- Dependencies:
  - Must verify compatibility with the target runtime before adding.
  - Prefer testing imports locally before committing.
  - For untyped libraries, prefer explicit `# type: ignore[import-untyped]` on the import.
- Logging:
  - Must enforce the logging formatting rule; no workarounds.
- Cleanup:
  - Must remove unused variables/imports promptly.
  - Must not leave dead code.
- Stability:
  - Must not change externally-visible strings/outputs unless intentional and reviewed.

Learned rules
- Must keep contract-sensitive error messages stable; tests may assert exact strings.
- Must not change exit codes for existing failure scenarios.

Repo additions
- Project name: living-doc-collector-gh
- Purpose: Python GitHub Action that collects “living documentation” data from GitHub (e.g., Projects/Issues) and writes machine-readable JSON for downstream documentation generation.
- Runtime: Python 3.14+
- Logging rule:
  - Must use lazy `%` formatting (e.g., `logger.info("msg %s", value)`).
  - Must not use f-strings for logging interpolation.
- Imports:
  - Must place all Python imports at the top of the file (not inside functions/methods).
- Entry points:
  - `main.py`
- Inputs:
  - Via `INPUT_*` environment variables (see `action.yml`).
- Outputs:
  - Must write under the repository's configured output folder (see code that uses `OUTPUT_PATH`).
  - Contract-sensitive output: action output `output-path`.
- Tooling commands (canonical):
  - Tests: `pytest tests/`
  - Format: `black $(git ls-files '*.py')`
  - Lint (exclude tests): `pylint $(git ls-files '*.py' ':!:tests/**')`
  - Types: `mypy .` (or `mypy <changed_files>`)
  - Coverage: `pytest --ignore=tests/integration --cov=. tests/ --cov-fail-under=80 --cov-report=html`
- Thresholds:
  - Pylint score: >= 9.5/10
  - Coverage: >= 80%
- Allowed exceptions to this template: none
