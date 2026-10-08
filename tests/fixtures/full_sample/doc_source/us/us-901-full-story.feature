# Fully authored fixture (R12 check 3): every User Story header key and every AC extension.
# =============================================================================
# LIVING DOC — US-901 · Fully Authored Story
# =============================================================================
# source:         https://github.com/AbsaOSS/living-doc-collector-gh/issues/901
# status:         active
# business_value:
#   - Every field of the doc-source contract is exercised by one story.
# preconditions:
#   - The collector runs over this fixture.
# not_in_scope:
#   - Issue-body authoring, which the doc-issues mode will read.
# notes:
#   - This story exists only to fill every contract field.
#
# acceptance_criteria:
#
#   AC:US-901-01 (v1.0.0 - active)
#     - A fully authored criterion carries every extension.
#     - Aspect: desktop, mobile
#     - Rationale: Every extension field needs one authored value.
#     preconditions:
#       - The story is active.
#     not_in_scope:
#       - Rendering of the criterion.
#
#   AC:US-901-02 (v1.0.0 – active)
#     - A criterion written with a non-canonical dash is still read.
#
#   AC:US-901-03 (v1.1.0 - planned)
#     - A planned criterion targeted at a version.
#
#   AC:US-901-04 (planned)
#     - A planned backlog criterion with no version.
#
#   AC:US-901-05 (v1.0.0 - deprecated - removal planned v2.0.0)
#     - A deprecated criterion with its planned removal version.
#
#   AC:US-901-06 (v1.0.0 - active)
#     - The story is readable for every {user role}.
#     - User role: admin, viewer, auditor
# =============================================================================

@US_ID:US-901
Feature: Fully Authored Story
  As a maintainer, I can check every contract field, so that no field is lost.
