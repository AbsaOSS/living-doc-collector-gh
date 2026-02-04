# Copilot Review Rules

## Purpose

- Do define consistent review behavior and response formatting for Copilot code reviews across repositories.
- Avoid long audit reports unless explicitly requested.

## Writing style

- Do use short headings and bullet lists.
- Do prefer “do/avoid” constraints over prose.
- Do make checks verifiable (reviewer can point to code and impact).
- Avoid rewriting entire PRs; prefer minimal actionable suggestions.

## Review modes

This template defines two modes:

- Default review: standard PR risk
- Double-check review: elevated risk PRs

## Mode: Default review

- Scope
  - Do review a single PR at normal risk.
- Priorities (in order)
  - Do prioritize: correctness → security → tests → maintainability → style.
- Checks
  - Correctness
    - Do highlight logic bugs, missing edge cases, regressions, and contract changes.
  - Security & data handling
    - Do flag unsafe input handling, secrets exposure, auth/authz issues, and insecure defaults.
  - Tests
    - Do check that tests exist for changed logic and cover success + failure paths.
  - Maintainability
    - Do point out unnecessary complexity, duplication, and unclear naming/structure.
  - Style
    - Do note style issues only when they reduce readability or break repo conventions.
- Response format
  - Do use short bullet points.
  - Do reference files + line ranges where possible.
  - Do group comments by severity:
    - Blocker (must fix)
    - Important (should fix)
    - Nit (optional)
  - Do provide actionable suggestions (what to change), not rewrites.
  - Avoid producing long reports.

## Mode: Double-check review

- Scope
  - Do use for higher-risk PRs (security, infra, money flows, wide refactors, data migrations, auth changes).
- Additional focus
  - Do confirm previous review comments were correctly addressed (if applicable).
  - Do re-check high-risk areas:
    - auth, permissions, secrets, money transfers/billing, persistence, external calls, concurrency
  - Do look for hidden side effects:
    - backward compatibility, rollout/upgrade path, failure modes, retries/timeouts, idempotency
  - Do validate safe defaults:
    - least privilege, secure logging, safe error messages, predictable behavior on missing inputs
- Response format
  - Do add comments only where risk/impact is non-trivial.
  - Avoid repeating minor style notes already covered by default review.
  - Do call out “risk acceptance” explicitly if something is left as-is:
    - what risk
    - why acceptable
    - what mitigation exists (tests/monitoring/feature flag)

## Commenting rules (applies to all modes)

- Do always include:
  - What is the issue (1 line)
  - Why it matters (impact/risk)
  - How to fix (minimal actionable suggestion)
- Do prefer linking to existing patterns in the repo over introducing new ones.
- If you cannot be certain (missing context), do ask a targeted question instead of assuming.

## Non-goals

- Avoid requesting refactors unrelated to the PR’s intent.
- Avoid bikeshedding formatting if tools (formatter/linter) handle it.
- Avoid proposing architectural rewrites unless explicitly requested.

## Repo additions (living-doc-collector-gh)

- Domain-specific high-risk areas
  - GitHub Action contracts and runner environment behavior.
  - External calls to GitHub APIs (must be mocked in unit tests).
- Contract-sensitive surfaces
  - `action.yml` inputs → `INPUT_*` environment variables.
  - Action output `output-path`.
  - JSON outputs and any schema-like structures (keep stable unless explicitly changed).
  - Exact error messages and exit code behavior (tests may assert exact strings/codes).
- Required test expectations
  - Unit tests live under `tests/`.
  - Tests should cover success + failure paths for changed logic.

